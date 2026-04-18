from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('questions', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='question',
            index=models.Index(
                fields=['level', 'is_active'],
                name='question_level_active_idx',
            ),
        ),
    ]
