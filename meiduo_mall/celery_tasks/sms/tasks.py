# 定义耗时的异步任务
from .yuntongxun.sms import CCP
from . import constants
from celery_tasks.main import celery_app


# 使用task装饰器，将以下任务装饰为诶celery可以识别的异步任务
# task(name='send_sms_code') ： 给异步任务起别名，如果不起别名毫无影响，但是异步任务的默认的名字会很长
@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    """
    定义发短信异步任务
    :param mobile: 手机号
    :param sms_code: 短信验证码
    :return: None
    """
    CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)