from django.db import models
from django.contrib.auth.models import User
from apps.knowledge.models import GespLevel, KnowledgePoint


class Question(models.Model):
    TYPE_CHOICES = [
        (1, '单选题'),
        (2, '多选题'),
        (3, '判断题'),
    ]
    DIFFICULTY_CHOICES = [
        (1, '简单'),
        (2, '中等'),
        (3, '困难'),
    ]
    level = models.ForeignKey(GespLevel, on_delete=models.CASCADE, related_name='questions', verbose_name='级别')
    question_type = models.PositiveSmallIntegerField('题目类型', choices=TYPE_CHOICES)
    difficulty = models.PositiveSmallIntegerField('难度', choices=DIFFICULTY_CHOICES, default=1)
    content = models.TextField('题目内容')
    options = models.JSONField('选项', default=list, blank=True)
    answer = models.CharField('正确答案', max_length=10)
    explanation = models.TextField('解析', blank=True, default='')
    source = models.CharField('来源', max_length=100, blank=True, default='')
    knowledge_points = models.ManyToManyField(KnowledgePoint, blank=True, related_name='questions', verbose_name='关联知识点')
    is_active = models.BooleanField('是否启用', default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'question'
        verbose_name = '题目'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['level', 'question_type']),
            models.Index(fields=['difficulty']),
        ]

    def __str__(self):
        return f'[{self.get_question_type_display()}] {self.content[:50]}'
