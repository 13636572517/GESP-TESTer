from django.db import models
from django.contrib.auth.models import User
from apps.knowledge.models import KnowledgePoint


class UserKnowledgeMastery(models.Model):
    MASTERY_CHOICES = [
        (0, '未学'),
        (1, '入门'),
        (2, '熟悉'),
        (3, '掌握'),
        (4, '精通'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mastery_records', verbose_name='用户')
    knowledge = models.ForeignKey(KnowledgePoint, on_delete=models.CASCADE, verbose_name='知识点')
    total_attempts = models.PositiveIntegerField('总做题次数', default=0)
    correct_count = models.PositiveIntegerField('正确次数', default=0)
    mastery_level = models.PositiveSmallIntegerField('掌握等级', choices=MASTERY_CHOICES, default=0)
    last_practiced = models.DateTimeField('最近练习时间', null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_knowledge_mastery'
        verbose_name = '知识点掌握度'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'knowledge']

    def update_mastery(self):
        """根据正确率计算掌握等级"""
        if self.total_attempts == 0:
            self.mastery_level = 0
            return
        rate = self.correct_count / self.total_attempts
        if rate < 0.4:
            self.mastery_level = 1
        elif rate < 0.6:
            self.mastery_level = 2
        elif rate < 0.85:
            self.mastery_level = 3
        elif self.total_attempts >= 10:
            self.mastery_level = 4
        else:
            self.mastery_level = 3


class DailyStudyLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_logs', verbose_name='用户')
    study_date = models.DateField('学习日期')
    practice_count = models.PositiveIntegerField('练习题数', default=0)
    correct_count = models.PositiveIntegerField('正确题数', default=0)
    exam_count = models.PositiveIntegerField('模考次数', default=0)
    study_minutes = models.PositiveIntegerField('学习时长(分钟)', default=0)

    class Meta:
        db_table = 'daily_study_log'
        verbose_name = '每日学习记录'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'study_date']
