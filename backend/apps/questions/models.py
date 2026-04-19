from django.db import models
from django.contrib.auth.models import User
from apps.knowledge.models import GespLevel, KnowledgePoint


class AIConfig(models.Model):
    """AI 服务全局配置（单行配置表）"""
    api_key   = models.CharField('API Key', max_length=300, blank=True, default='')
    tag_model = models.CharField('标注模型', max_length=100, default='qwen-plus')
    gen_model = models.CharField('出题模型', max_length=100, default='qwen-plus')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='最后修改者'
    )

    class Meta:
        db_table = 'ai_config'
        verbose_name = 'AI配置'

    def __str__(self):
        return f'AI配置（标注:{self.tag_model} 出题:{self.gen_model}）'


class AIUsageLog(models.Model):
    """AI 调用用量日志"""
    OP_TAG     = 1
    OP_GEN     = 2
    OP_TEST    = 3
    OP_EXPLAIN = 4
    OPERATION_CHOICES = [
        (OP_TAG,     '知识点标注'),
        (OP_GEN,     'AI出题'),
        (OP_TEST,    '模型测试'),
        (OP_EXPLAIN, 'AI题目讲解'),
    ]

    operation          = models.PositiveSmallIntegerField('操作类型', choices=OPERATION_CHOICES)
    model              = models.CharField('模型', max_length=100)
    prompt_tokens      = models.IntegerField('输入Token', default=0)
    completion_tokens  = models.IntegerField('输出Token', default=0)
    total_tokens       = models.IntegerField('总Token', default=0)
    success            = models.BooleanField('成功', default=True)
    latency_ms         = models.IntegerField('响应时间ms', default=0)
    error_msg          = models.TextField('错误信息', blank=True, default='')
    # user=None 表示管理员全局调用，user=xxx 表示该用户自己的调用
    user               = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='ai_usage_logs', verbose_name='使用用户'
    )
    created_at         = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_usage_log'
        verbose_name = 'AI用量日志'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['created_at', 'operation'])]

    def __str__(self):
        return f'[{self.get_operation_display()}] {self.model} {self.total_tokens}tok'


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
    SOURCE_TYPE_CHOICES = [
        (1, '真题'),
        (2, 'AI生成'),
    ]
    level = models.ForeignKey(GespLevel, on_delete=models.CASCADE, related_name='questions', verbose_name='级别')
    question_type = models.PositiveSmallIntegerField('题目类型', choices=TYPE_CHOICES)
    difficulty = models.PositiveSmallIntegerField('难度', choices=DIFFICULTY_CHOICES, default=1)
    content = models.TextField('题目内容')
    options = models.JSONField('选项', default=list, blank=True)
    answer = models.CharField('正确答案', max_length=10)
    explanation = models.TextField('解析', blank=True, default='')
    source = models.CharField('来源', max_length=100, blank=True, default='')
    source_type = models.PositiveSmallIntegerField('题目来源类型', choices=SOURCE_TYPE_CHOICES, default=1)
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


class QuestionFeedback(models.Model):
    TYPE_ANSWER_WRONG  = 1
    TYPE_CONTENT_UNCLEAR = 2
    TYPE_OPTION_ISSUE  = 3
    TYPE_OTHER         = 4
    TYPE_CHOICES = [
        (TYPE_ANSWER_WRONG,    '答案有误'),
        (TYPE_CONTENT_UNCLEAR, '题目表述不清'),
        (TYPE_OPTION_ISSUE,    '选项有问题'),
        (TYPE_OTHER,           '其他'),
    ]
    STATUS_PENDING  = 0
    STATUS_HANDLED  = 1
    STATUS_IGNORED  = 2
    STATUS_CHOICES = [
        (STATUS_PENDING, '待处理'),
        (STATUS_HANDLED, '已处理'),
        (STATUS_IGNORED, '已忽略'),
    ]

    question      = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='feedbacks', verbose_name='题目')
    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks', verbose_name='反馈用户')
    feedback_type = models.PositiveSmallIntegerField('反馈类型', choices=TYPE_CHOICES)
    content       = models.TextField('反馈内容', blank=True, default='')
    status        = models.PositiveSmallIntegerField('处理状态', choices=STATUS_CHOICES, default=STATUS_PENDING)
    admin_reply   = models.TextField('管理员回复', blank=True, default='')
    created_at    = models.DateTimeField(auto_now_add=True)
    handled_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'question_feedback'
        verbose_name = '题目反馈'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.get_feedback_type_display()}] Q{self.question_id} by {self.user}'
