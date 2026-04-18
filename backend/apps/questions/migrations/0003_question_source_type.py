from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0002_question_level_active_idx'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='source_type',
            field=models.PositiveSmallIntegerField(
                choices=[(1, '真题'), (2, 'AI生成')],
                default=1,
                verbose_name='题目来源类型',
            ),
        ),
        migrations.AddIndex(
            model_name='question',
            index=models.Index(
                fields=['level', 'source_type', 'is_active'],
                name='question_level_src_active_idx',
            ),
        ),
    ]
