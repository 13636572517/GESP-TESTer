from django.db import models
from django.contrib.auth.models import User
from apps.knowledge.models import GespLevel


class ProgrammingQuestion(models.Model):
    DIFFICULTY_CHOICES = [(1, '简单'), (2, '中等'), (3, '困难')]

    level = models.ForeignKey(GespLevel, on_delete=models.CASCADE, related_name='programming_questions', verbose_name='级别')
    title = models.CharField('标题', max_length=200)
    description = models.TextField('题目描述（Markdown）')
    input_description = models.TextField('输入说明', blank=True, default='')
    output_description = models.TextField('输出说明', blank=True, default='')
    difficulty = models.PositiveSmallIntegerField('难度', choices=DIFFICULTY_CHOICES, default=1)
    time_limit = models.IntegerField('时间限制(ms)', default=1000)
    memory_limit = models.IntegerField('内存限制(MB)', default=256)
    is_active = models.BooleanField('启用', default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'programming_question'
        verbose_name = '编程题'
        ordering = ['level', 'difficulty', 'id']

    def __str__(self):
        return self.title


class TestCase(models.Model):
    question = models.ForeignKey(ProgrammingQuestion, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField('输入', blank=True, default='')
    expected_output = models.TextField('期望输出')
    is_sample = models.BooleanField('样例（对用户可见）', default=False)
    order = models.IntegerField('排序', default=0)

    class Meta:
        db_table = 'programming_test_case'
        ordering = ['order', 'id']

    def __str__(self):
        return f'TestCase #{self.pk} for {self.question_id}'


class CodeSubmission(models.Model):
    STATUS_PENDING = 1
    STATUS_RUNNING = 2
    STATUS_ACCEPTED = 3
    STATUS_WRONG = 4
    STATUS_TLE = 5
    STATUS_MLE = 6
    STATUS_RE = 7
    STATUS_CE = 8
    STATUS_ERROR = 13

    STATUS_CHOICES = [
        (STATUS_PENDING, '等待中'),
        (STATUS_RUNNING, '运行中'),
        (STATUS_ACCEPTED, '通过'),
        (STATUS_WRONG, '答案错误'),
        (STATUS_TLE, '超时'),
        (STATUS_MLE, '内存超限'),
        (STATUS_RE, '运行错误'),
        (STATUS_CE, '编译错误'),
        (STATUS_ERROR, '系统错误'),
    ]

    LANGUAGE_CPP = 54  # C++ (GCC 9.2.0)

    question = models.ForeignKey(ProgrammingQuestion, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='code_submissions')
    code = models.TextField('代码')
    language_id = models.IntegerField('语言ID', default=LANGUAGE_CPP)
    judge0_token = models.CharField('Judge0 Token', max_length=100, blank=True, default='')
    status = models.IntegerField('状态', choices=STATUS_CHOICES, default=STATUS_PENDING)
    stdout = models.TextField('输出', blank=True, default='')
    stderr = models.TextField('错误', blank=True, default='')
    compile_output = models.TextField('编译输出', blank=True, default='')
    time_used = models.FloatField('运行时间(s)', null=True, blank=True)
    memory_used = models.IntegerField('内存(KB)', null=True, blank=True)
    passed_cases = models.IntegerField('通过测试点', default=0)
    total_cases = models.IntegerField('总测试点', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'programming_submission'
        ordering = ['-created_at']

    def __str__(self):
        return f'Submission #{self.pk} by {self.user_id}'
