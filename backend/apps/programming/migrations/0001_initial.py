from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('knowledge', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgrammingQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='标题')),
                ('description', models.TextField(verbose_name='题目描述（Markdown）')),
                ('input_description', models.TextField(blank=True, default='', verbose_name='输入说明')),
                ('output_description', models.TextField(blank=True, default='', verbose_name='输出说明')),
                ('difficulty', models.PositiveSmallIntegerField(choices=[(1, '简单'), (2, '中等'), (3, '困难')], default=1, verbose_name='难度')),
                ('time_limit', models.IntegerField(default=1000, verbose_name='时间限制(ms)')),
                ('memory_limit', models.IntegerField(default=256, verbose_name='内存限制(MB)')),
                ('is_active', models.BooleanField(default=True, verbose_name='启用')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='programming_questions', to='knowledge.gesplevel', verbose_name='级别')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.user')),
            ],
            options={'db_table': 'programming_question', 'verbose_name': '编程题', 'ordering': ['level', 'difficulty', 'id']},
        ),
        migrations.CreateModel(
            name='TestCase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('input_data', models.TextField(blank=True, default='', verbose_name='输入')),
                ('expected_output', models.TextField(verbose_name='期望输出')),
                ('is_sample', models.BooleanField(default=False, verbose_name='样例（对用户可见）')),
                ('order', models.IntegerField(default=0, verbose_name='排序')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_cases', to='programming.programmingquestion')),
            ],
            options={'db_table': 'programming_test_case', 'ordering': ['order', 'id']},
        ),
        migrations.CreateModel(
            name='CodeSubmission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.TextField(verbose_name='代码')),
                ('language_id', models.IntegerField(default=54, verbose_name='语言ID')),
                ('judge0_token', models.CharField(blank=True, default='', max_length=100, verbose_name='Judge0 Token')),
                ('status', models.IntegerField(choices=[(1, '等待中'), (2, '运行中'), (3, '通过'), (4, '答案错误'), (5, '超时'), (6, '内存超限'), (7, '运行错误'), (8, '编译错误'), (13, '系统错误')], default=1, verbose_name='状态')),
                ('stdout', models.TextField(blank=True, default='', verbose_name='输出')),
                ('stderr', models.TextField(blank=True, default='', verbose_name='错误')),
                ('compile_output', models.TextField(blank=True, default='', verbose_name='编译输出')),
                ('time_used', models.FloatField(blank=True, null=True, verbose_name='运行时间(s)')),
                ('memory_used', models.IntegerField(blank=True, null=True, verbose_name='内存(KB)')),
                ('passed_cases', models.IntegerField(default=0, verbose_name='通过测试点')),
                ('total_cases', models.IntegerField(default=0, verbose_name='总测试点')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='programming.programmingquestion')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='code_submissions', to='auth.user')),
            ],
            options={'db_table': 'programming_submission', 'ordering': ['-created_at']},
        ),
    ]
