from django.db import models
from django.contrib.auth.models import User
from apps.knowledge.models import GespLevel
from apps.questions.models import Question


class PracticeSession(models.Model):
    TYPE_CHOICES = [
        (1, '知识点专练'),
        (2, '随机组题'),
        (3, '错题复习'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='practice_sessions', verbose_name='用户')
    session_type = models.PositiveSmallIntegerField('练习类型', choices=TYPE_CHOICES)
    level = models.ForeignKey(GespLevel, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='级别')
    total_count = models.PositiveIntegerField('总题数', default=0)
    correct_count = models.PositiveIntegerField('正确数', default=0)
    finished_at = models.DateTimeField('完成时间', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'practice_session'
        verbose_name = '练习记录'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['user']),
        ]


class PracticeAnswer(models.Model):
    session = models.ForeignKey(PracticeSession, on_delete=models.CASCADE, related_name='answers', verbose_name='练习记录')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='题目')
    user_answer = models.CharField('用户答案', max_length=10, blank=True, default='')
    is_correct = models.BooleanField('是否正确', null=True)
    time_spent = models.PositiveIntegerField('答题用时(秒)', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'practice_answer'
        verbose_name = '练习答题明细'
        verbose_name_plural = verbose_name


class MistakeRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mistakes', verbose_name='用户')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='题目')
    wrong_count = models.PositiveIntegerField('累计错误次数', default=1)
    last_wrong_answer = models.CharField('最近错误答案', max_length=10, blank=True, default='')
    is_mastered = models.BooleanField('是否已掌握', default=False)
    consecutive_correct = models.PositiveIntegerField('连续正确次数', default=0)
    last_practiced_at = models.DateTimeField('最近练习时间', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mistake_record'
        verbose_name = '错题记录'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'question']
        indexes = [
            models.Index(fields=['user', 'is_mastered']),
        ]
