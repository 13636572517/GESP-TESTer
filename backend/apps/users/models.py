from django.db import models
from django.contrib.auth.models import User
from apps.knowledge.models import GespLevel


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField('手机号', max_length=11, unique=True, null=True, blank=True, default=None)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, default='')
    nickname = models.CharField('昵称', max_length=50, blank=True, default='')
    current_level = models.PositiveSmallIntegerField('当前学习级别', default=1)
    is_admin = models.BooleanField('是否管理员', default=False)
    is_teacher = models.BooleanField('是否老师', default=False)
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


class Classroom(models.Model):
    name = models.CharField('班级名称', max_length=100)
    description = models.CharField('描述', max_length=300, blank=True, default='')
    level = models.ForeignKey(GespLevel, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='classrooms', verbose_name='对应级别')
    teachers = models.ManyToManyField(
        'auth.User', blank=True,
        related_name='teaching_classrooms',
        verbose_name='授课老师',
    )
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'classroom'
        verbose_name = '班级'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def member_count(self):
        return self.members.count()


class UserAIConfig(models.Model):
    """普通用户自己的 AI 配置（一人一行）"""
    user      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='ai_config')
    api_key   = models.TextField('API Key（加密存储）', blank=True, default='')
    tag_model = models.CharField('标注模型', max_length=100, default='qwen-plus')
    gen_model = models.CharField('出题模型', max_length=100, default='qwen-plus')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_ai_config'
        verbose_name = '用户AI配置'

    def __str__(self):
        return f'{self.user.username} AI配置'


class ClassroomMember(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='members', verbose_name='班级')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classrooms', verbose_name='学员')
    note = models.CharField('备注', max_length=200, blank=True, default='')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'classroom_member'
        verbose_name = '班级成员'
        verbose_name_plural = verbose_name
        unique_together = [('classroom', 'user')]
        ordering = ['joined_at']
