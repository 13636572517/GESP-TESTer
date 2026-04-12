from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField('手机号', max_length=11, unique=True)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, default='')
    nickname = models.CharField('昵称', max_length=50, blank=True, default='')
    current_level = models.PositiveSmallIntegerField('当前学习级别', default=1)
    is_admin = models.BooleanField('是否管理员', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profile'
        verbose_name = '用户资料'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.nickname or self.phone}'


class SmsCode(models.Model):
    PURPOSE_CHOICES = [
        ('register', '注册'),
        ('login', '登录'),
        ('reset_password', '重置密码'),
    ]
    phone = models.CharField('手机号', max_length=11, db_index=True)
    code = models.CharField('验证码', max_length=6)
    purpose = models.CharField('用途', max_length=20, choices=PURPOSE_CHOICES)
    is_used = models.BooleanField('是否已使用', default=False)
    expired_at = models.DateTimeField('过期时间')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sms_code'
        verbose_name = '短信验证码'
        verbose_name_plural = verbose_name
