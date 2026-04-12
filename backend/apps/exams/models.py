from django.db import models
from django.contrib.auth.models import User
from apps.knowledge.models import GespLevel
from apps.questions.models import Question


class ExamTemplate(models.Model):
    TYPE_CHOICES = [
        (1, '真题'),
        (2, '模拟卷'),
    ]
    name = models.CharField('试卷名称', max_length=200)
    level = models.ForeignKey(GespLevel, on_delete=models.CASCADE, related_name='exam_templates', verbose_name='级别')
    duration = models.PositiveIntegerField('考试时长(分钟)')
    total_score = models.PositiveIntegerField('总分', default=100)
    pass_score = models.PositiveIntegerField('及格分', default=60)
    is_active = models.BooleanField('是否启用', default=True)
    template_type = models.PositiveSmallIntegerField('试卷类型', choices=TYPE_CHOICES, default=1)
    questions = models.ManyToManyField(Question, through='ExamTemplateQuestion', verbose_name='题目')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exam_template'
        verbose_name = '试卷模板'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class ExamTemplateQuestion(models.Model):
    template = models.ForeignKey(ExamTemplate, on_delete=models.CASCADE, related_name='template_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    score = models.PositiveIntegerField('分值', default=2)
    sort_order = models.PositiveIntegerField('排序', default=0)

    class Meta:
        db_table = 'exam_template_question'
        verbose_name = '试卷题目'
        verbose_name_plural = verbose_name
        ordering = ['sort_order']


class ExamRecord(models.Model):
    STATUS_CHOICES = [
        (0, '进行中'),
        (1, '已交卷'),
        (2, '超时自动交卷'),
    ]
    EXAM_TYPE_CHOICES = [
        (1, '真题模拟'),
        (2, '随机组卷'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_records', verbose_name='用户')
    template = models.ForeignKey(ExamTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='试卷模板')
    level = models.ForeignKey(GespLevel, on_delete=models.CASCADE, verbose_name='级别')
    exam_type = models.PositiveSmallIntegerField('考试类型', choices=EXAM_TYPE_CHOICES, default=1)
    duration = models.PositiveIntegerField('考试时长(分钟)')
    start_time = models.DateTimeField('开始时间')
    end_time = models.DateTimeField('结束时间', null=True, blank=True)
    total_score = models.PositiveIntegerField('总分', default=0)
    earned_score = models.PositiveIntegerField('得分', default=0)
    status = models.PositiveSmallIntegerField('状态', choices=STATUS_CHOICES, default=0)
    switch_count = models.PositiveIntegerField('切屏次数', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'exam_record'
        verbose_name = '考试记录'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
        ]


class ExamAnswer(models.Model):
    record = models.ForeignKey(ExamRecord, on_delete=models.CASCADE, related_name='answers', verbose_name='考试记录')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='题目')
    user_answer = models.CharField('用户答案', max_length=10, blank=True, default='')
    is_correct = models.BooleanField('是否正确', null=True)
    score = models.PositiveIntegerField('得分', default=0)
    time_spent = models.PositiveIntegerField('答题用时(秒)', default=0)

    class Meta:
        db_table = 'exam_answer'
        verbose_name = '考试答题明细'
        verbose_name_plural = verbose_name
