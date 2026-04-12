from django.db import models


class GespLevel(models.Model):
    id = models.PositiveSmallIntegerField('级别', primary_key=True)
    name = models.CharField('名称', max_length=50)
    description = models.TextField('描述', blank=True, default='')
    exam_duration = models.PositiveIntegerField('考试时长(分钟)', default=90)
    total_questions = models.PositiveIntegerField('考试题目数', default=50)
    pass_score = models.PositiveIntegerField('及格分', default=60)

    class Meta:
        db_table = 'gesp_level'
        verbose_name = 'GESP级别'
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return self.name


class Chapter(models.Model):
    level = models.ForeignKey(GespLevel, on_delete=models.CASCADE, related_name='chapters', verbose_name='级别')
    name = models.CharField('章节名称', max_length=100)
    sort_order = models.PositiveIntegerField('排序', default=0)

    class Meta:
        db_table = 'chapter'
        verbose_name = '章节'
        verbose_name_plural = verbose_name
        ordering = ['level', 'sort_order']

    def __str__(self):
        return f'{self.level.name} - {self.name}'


class KnowledgePoint(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='points', verbose_name='章节')
    name = models.CharField('知识点名称', max_length=200)
    description = models.TextField('简要说明', blank=True, default='')
    content = models.TextField('讲解内容(富文本)', blank=True, default='')
    sort_order = models.PositiveIntegerField('排序', default=0)

    class Meta:
        db_table = 'knowledge_point'
        verbose_name = '知识点'
        verbose_name_plural = verbose_name
        ordering = ['chapter', 'sort_order']

    def __str__(self):
        return self.name
