import csv
import io
import re
from html import escape as html_escape
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.db import models as db_models
from .models import GespLevel, Chapter, KnowledgePoint
from .serializers import (
    GespLevelSerializer, ChapterSerializer,
    KnowledgePointSerializer, KnowledgePointDetailSerializer,
    KnowledgeTreeSerializer, KnowledgeContentUpdateSerializer,
)


class AdminPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return hasattr(request.user, 'profile') and request.user.profile.is_admin


def convert_code_markers(text):
    """Convert backtick-marked code to HTML tags."""
    if not text or '<pre' in text or '<code' in text:
        return text
    text = re.sub(
        r'```(?:\w+\n)?(.*?)```',
        lambda m: '<pre>' + html_escape(m.group(1).strip()) + '</pre>',
        text, flags=re.DOTALL,
    )
    text = re.sub(
        r'`([^`]+)`',
        lambda m: '<code>' + html_escape(m.group(1)) + '</code>',
        text,
    )
    return text


class LevelListView(generics.ListAPIView):
    queryset = GespLevel.objects.all()
    serializer_class = GespLevelSerializer
    permission_classes = [AllowAny]


class ChapterListView(generics.ListAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Chapter.objects.filter(level_id=self.kwargs['level_id']).prefetch_related('points')


class KnowledgePointListView(generics.ListAPIView):
    serializer_class = KnowledgePointSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return KnowledgePoint.objects.filter(chapter_id=self.kwargs['chapter_id'])


class KnowledgePointDetailView(generics.RetrieveAPIView):
    queryset = KnowledgePoint.objects.select_related('chapter__level')
    serializer_class = KnowledgePointDetailSerializer
    permission_classes = [AllowAny]


@api_view(['GET'])
@permission_classes([AllowAny])
def knowledge_tree(request):
    levels = GespLevel.objects.prefetch_related('chapters__points').all()
    serializer = KnowledgeTreeSerializer(levels, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_knowledge_content(request, pk):
    """管理员编辑知识点讲解内容"""
    if not hasattr(request.user, 'profile') or not request.user.profile.is_admin:
        return Response({'detail': '无权限'}, status=403)

    try:
        point = KnowledgePoint.objects.get(pk=pk)
    except KnowledgePoint.DoesNotExist:
        return Response({'detail': '知识点不存在'}, status=404)

    serializer = KnowledgeContentUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    point.content = serializer.validated_data['content']
    point.save(update_fields=['content'])
    return Response({'detail': '更新成功'})


def _parse_level_id(raw):
    """Parse level from '1', 'GESP一级', 'GESP1级', '一级', '1级' etc."""
    raw = raw.strip()
    if not raw:
        return None
    # Pure digit
    if raw.isdigit():
        return int(raw)
    # Chinese numeral map
    cn_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8}
    for cn, num in cn_map.items():
        if cn in raw:
            return num
    # Try extract digit from string like 'GESP1级'
    m = re.search(r'(\d+)', raw)
    if m:
        return int(m.group(1))
    return None


@api_view(['POST'])
@permission_classes([AdminPermission])
def import_knowledge_csv(request):
    """CSV文件导入知识点"""
    file = request.FILES.get('file')
    if not file:
        return Response({'detail': '请上传CSV文件'}, status=400)
    if not file.name.endswith('.csv'):
        return Response({'detail': '仅支持CSV格式文件'}, status=400)

    try:
        content = file.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            file.seek(0)
            content = file.read().decode('gbk')
        except UnicodeDecodeError:
            return Response({'detail': '文件编码不支持，请使用UTF-8或GBK编码'}, status=400)

    # Strip any remaining BOM characters
    content = content.replace('\ufeff', '')
    reader = csv.DictReader(io.StringIO(content))

    created_count = 0
    updated_count = 0
    errors = []

    for i, row in enumerate(reader):
        try:
            # Parse level
            level_raw = row.get('级别', '').strip()
            level_id = _parse_level_id(level_raw)
            if not level_id or level_id < 1 or level_id > 8:
                errors.append({'row': i + 2, 'error': f'级别无效: {level_raw}'})
                continue

            # Get or create level
            level, _ = GespLevel.objects.get_or_create(
                id=level_id,
                defaults={'name': f'GESP{level_id}级'},
            )

            # Parse chapter
            chapter_name = row.get('章节', '').strip()
            if not chapter_name:
                errors.append({'row': i + 2, 'error': '章节名称不能为空'})
                continue

            # Get or create chapter
            chapter, ch_created = Chapter.objects.get_or_create(
                level=level,
                name=chapter_name,
                defaults={
                    'sort_order': (Chapter.objects.filter(level=level).aggregate(
                        max_order=db_models.Max('sort_order')
                    )['max_order'] or 0) + 1
                },
            )

            # Parse knowledge point
            point_name = row.get('知识点', '').strip()
            if not point_name:
                errors.append({'row': i + 2, 'error': '知识点名称不能为空'})
                continue

            description = row.get('描述', '').strip()
            raw_content = row.get('内容', '').strip()
            point_content = convert_code_markers(raw_content) if raw_content else ''
            sort_order_raw = row.get('排序', '').strip()
            sort_order = int(sort_order_raw) if sort_order_raw.isdigit() else 0

            # Update or create knowledge point
            defaults = {
                'description': description,
                'sort_order': sort_order,
            }
            if point_content:
                defaults['content'] = point_content

            point, pt_created = KnowledgePoint.objects.update_or_create(
                chapter=chapter,
                name=point_name,
                defaults=defaults,
            )

            if pt_created:
                created_count += 1
            else:
                updated_count += 1

        except Exception as e:
            errors.append({'row': i + 2, 'error': str(e)})

    return Response({
        'created_count': created_count,
        'updated_count': updated_count,
        'error_count': len(errors),
        'errors': errors[:50],
    })


@api_view(['GET'])
@permission_classes([AdminPermission])
def download_knowledge_csv_template(request):
    """下载知识点CSV导入模板"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="knowledge_template.csv"'
    response.write('\ufeff')  # BOM for Excel

    writer = csv.writer(response)
    writer.writerow(['级别', '章节', '知识点', '描述', '内容', '排序'])
    writer.writerow(['1', '顺序结构', 'cout输出语句', '学习基本的输出方法', '使用 `cout` 进行标准输出，需要包含头文件 `<iostream>`。', '1'])
    writer.writerow(['1', '顺序结构', 'cin输入语句', '学习基本的输入方法', '使用 `cin` 读取用户输入。', '2'])
    writer.writerow(['2', '循环结构', 'for循环', '掌握for循环的基本用法', '```cpp\nfor (int i = 0; i < n; i++) {\n    cout << i;\n}\n```', '1'])

    return response


@api_view(['GET'])
@permission_classes([AdminPermission])
def export_knowledge_csv(request):
    """导出知识点为CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="knowledge_export.csv"'
    response.write('\ufeff')  # BOM for Excel

    writer = csv.writer(response)
    writer.writerow(['级别', '章节', '知识点', '描述', '内容', '排序'])

    qs = KnowledgePoint.objects.select_related('chapter__level').order_by(
        'chapter__level__id', 'chapter__sort_order', 'sort_order'
    )

    # Optional level filter
    level = request.query_params.get('level')
    if level:
        qs = qs.filter(chapter__level_id=level)

    for point in qs:
        writer.writerow([
            point.chapter.level.id,
            point.chapter.name,
            point.name,
            point.description or '',
            point.content or '',
            point.sort_order,
        ])

    return response
