from django.shortcuts import render
from rest_framework.views import APIView
import random, logging
from django_redis import get_redis_connection
from . import constants
from meiduo_mall.libs.yuntongxun.sms import CCP
from rest_framework.response import Response
from rest_framework import status
from celery_tasks.sms.tasks import send_sms_code
# Create your views here.


# 使用配置信息中的django别名，创建一个日志输出器
logger = logging.getLogger('django')

class SMSCodeView(APIView):
    """发送短信验证码"""

    def get(self, request, mobile):
        """
        GET /sms_codes/(?P<mobile>1[3-9]\d{9})/
        """

        # 创建连接到redis的对象
        redis_conn = get_redis_connection('verify_codes')

        # 先判断用户在60s内是否重复发送短信
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            # 如果send_flag有值，说明60s内重复发送短信
            return Response({'message':'频繁发送短信'}, status=status.HTTP_400_BAD_REQUEST)

        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)

        # redis管道:将多个redis指令放在一个管道里面，统一执行，减少redis数据库访问的频率，提升性能
        pl = redis_conn.pipeline()

        # 保存短信验证码到Redis
        # redis_conn.setex('key','过期时间','value')
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)

        # 再在redis中添加一个发送短信的标记（值）
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 执行管道
        pl.execute()

        # 使用容联云通讯发送短信验证码
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)

        # 使用异步任务发送短信验证码
        # send_sms_code(mobile, sms_code) # 仅仅只是调用普通的函数而已，跟celery没有关系
        send_sms_code.delay(mobile, sms_code)   # 调用delay(),触发celery异步任务

        # 响应结果
        return Response({'message':'OK'})