"""
管理命令：为每个 GESP 级别创建"其他/无法分类"知识点。

用法：
    python manage.py seed_other_kp
"""
from django.core.management.base import BaseCommand
from apps.knowledge.models import GespLevel, Chapter, KnowledgePoint


class Command(BaseCommand):
    help = '为每个 GESP 级别添加"其他/无法分类"兜底知识点'

    def handle(self, *args, **options):
        for level_id in range(1, 9):
            level, _ = GespLevel.objects.get_or_create(
                id=level_id,
                defaults={'name': f'GESP{level_id}级'},
            )
            chapter, ch_created = Chapter.objects.get_or_create(
                level=level,
                name='其他',
                defaults={'sort_order': 999},
            )
            if ch_created:
                self.stdout.write(f'  创建章节：{level.name} > 其他')

            kp, kp_created = KnowledgePoint.objects.get_or_create(
                chapter=chapter,
                name='其他/无法分类',
                defaults={
                    'description': '无法归入现有知识点分类的题目，供 AI 或人工标注时兜底使用',
                    'sort_order': 999,
                },
            )
            status = '创建' if kp_created else '已存在'
            self.stdout.write(
                self.style.SUCCESS(f'  [{status}] {level.name} > 其他 > 其他/无法分类  (id={kp.id})')
            )

        self.stdout.write(self.style.SUCCESS('\n完成！共处理 8 个级别。'))
