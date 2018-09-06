from rest_framework import serializers
import re
from django_redis import get_redis_connection

from .models import User


class CreateUserSerialzier(serializers.ModelSerializer):

    # 定义模型外部字段
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)

    class Meta:
        model = User

        fields = ['id', 'username', 'mobile', 'password', 'password2',' sms_code', 'allow']

        # 给username和password指定额外参数
        extra_kwargs = {
            'username':{
                'min_length':5,
                'max_length':20,
                'error_messages':{
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password':{
                'write_only':True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate_mobile(self, value):
        """验证手机号"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def validate_allow(self, value):
        """检验用户是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, data):
        # 判断两次密码
        if data['password'] != data['password2']:
            raise serializers.ValidationError('两次密码不一致')

        # 判断短信验证码
        redis_conn = get_redis_connection('verify_codes')
        mobile = data['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if data['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return data

    def create(self, validated_data):
        """
        重写序列化器的create方法：因为有些字段不能默认往User里面存储
        :param validated_data: 经过校验之后的数据
        :return: user / 输出字段(read_only)：'id', 'username', 'mobile'
        """
        # 删除掉不需要保存到User里面的数据
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        # 自己实现保存数据到User
        user = User.objects.create(**validated_data)

        # 调用django的认证系统加密密码
        user.set_password(validated_data['password'])
        user.save()

        # 响应数据
        return user




