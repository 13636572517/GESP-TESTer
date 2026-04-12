import csv
import io
import json
import re
from html import escape as html_escape
from django.http import HttpResponse
from rest_framework import generics, status, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Question
from .serializers import QuestionSerializer, QuestionCreateSerializer


def convert_code_markers(text):
    """Convert backtick-marked code to HTML tags in question content.

    Supports:
      ```code```  or  ```cpp\\ncode\\n```  →  <pre>code</pre>
      `code`  →  <code>code</code>
    """
    if not text or '<pre' in text or '<code' in text:
        return text
    # Triple backticks → <pre> block
    # Language tag only consumed if followed by newline (e.g. ```cpp\n)
    text = re.sub(
        r'```(?:\w+\n)?(.*?)```',
        lambda m: '<pre>' + html_escape(m.group(1).strip()) + '</pre>',
        text,
        flags=re.DOTALL,
    )
    # Single backticks → <code> inline
    text = re.sub(
        r'`([^`]+)`',
        lambda m: '<code>' + html_escape(m.group(1)) + '</code>',
        text,
    )
    return text


class AdminPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return hasattr(request.user, 'profile') and request.user.profile.is_admin


class QuestionListCreateView(generics.ListCreateAPIView):
    permission_classes = [AdminPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content']
    ordering_fields = ['created_at', 'difficulty']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuestionCreateSerializer
        return QuestionSerializer

    def get_queryset(self):
        qs = Question.objects.select_related('level').all()
        level = self.request.query_params.get('level')
        qtype = self.request.query_params.get('type')
        difficulty = self.request.query_params.get('difficulty')
        knowledge = self.request.query_params.get('knowledge')
        search = self.request.query_params.get('search')

        if level:
            qs = qs.filter(level_id=level)
        if qtype:
            qs = qs.filter(question_type=qtype)
        if difficulty:
            qs = qs.filter(difficulty=difficulty)
        if knowledge:
            qs = qs.filter(knowledge_points__id=knowledge)
        if search:
            qs = qs.filter(content__icontains=search)
        return qs


class QuestionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    permission_classes = [AdminPermission]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return QuestionCreateSerializer
        return QuestionSerializer


@api_view(['POST'])
@permission_classes([AdminPermission])
def batch_create_questions(request):
    """批量导入题目（JSON格式）"""
    questions_data = request.data.get('questions', [])
    if not questions_data:
        return Response({'detail': '请提供题目数据'}, status=400)

    created = []
    errors = []
    for i, q_data in enumerate(questions_data):
        serializer = QuestionCreateSerializer(data=q_data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            created.append(serializer.data)
        else:
            errors.append({'index': i, 'errors': serializer.errors})

    return Response({
        'created_count': len(created),
        'error_count': len(errors),
        'errors': errors,
    })


@api_view(['POST'])
@permission_classes([AdminPermission])
def import_csv(request):
    """CSV文件导入题目"""
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

    reader = csv.DictReader(io.StringIO(content))

    TYPE_MAP = {'单选题': 1, '多选题': 2, '判断题': 3, '单选': 1, '多选': 2, '判断': 3}
    DIFF_MAP = {'简单': 1, '中等': 2, '困难': 3, '容易': 1}

    created = []
    errors = []

    for i, row in enumerate(reader):
        try:
            # 解析题型
            q_type_raw = row.get('题型', row.get('question_type', '')).strip()
            q_type = TYPE_MAP.get(q_type_raw) or int(q_type_raw) if q_type_raw else None

            # 解析难度
            diff_raw = row.get('难度', row.get('difficulty', '1')).strip()
            diff = DIFF_MAP.get(diff_raw) or int(diff_raw) if diff_raw else 1

            # 解析级别
            level_raw = row.get('级别', row.get('level', '')).strip()
            level_id = int(level_raw.replace('级', '')) if level_raw else None

            # 解析选项
            options = []
            if q_type != 3:
                for key in 'ABCDEF':
                    col_name = f'选项{key}'
                    alt_name = f'option_{key.lower()}'
                    text = row.get(col_name, row.get(alt_name, '')).strip()
                    if text:
                        options.append({'key': key, 'text': text})

            raw_content = row.get('题目', row.get('content', '')).strip()
            q_data = {
                'level': level_id,
                'question_type': q_type,
                'difficulty': diff,
                'content': convert_code_markers(raw_content),
                'options': options,
                'answer': row.get('答案', row.get('answer', '')).strip(),
                'explanation': row.get('解析', row.get('explanation', '')).strip(),
                'source': row.get('来源', row.get('source', '')).strip(),
            }

            serializer = QuestionCreateSerializer(data=q_data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                created.append(i)
            else:
                errors.append({'row': i + 2, 'errors': serializer.errors})
        except Exception as e:
            errors.append({'row': i + 2, 'errors': str(e)})

    return Response({
        'created_count': len(created),
        'error_count': len(errors),
        'errors': errors[:50],
    })


@api_view(['GET'])
@permission_classes([AdminPermission])
def export_questions(request):
    """导出题目（支持JSON和CSV格式）"""
    fmt = request.query_params.get('fmt', 'json')

    qs = Question.objects.select_related('level').prefetch_related('knowledge_points').all()

    # 应用筛选条件
    level = request.query_params.get('level')
    qtype = request.query_params.get('type')
    difficulty = request.query_params.get('difficulty')
    if level:
        qs = qs.filter(level_id=level)
    if qtype:
        qs = qs.filter(question_type=qtype)
    if difficulty:
        qs = qs.filter(difficulty=difficulty)

    if fmt == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="questions.csv"'
        response.write('\ufeff')  # BOM for Excel compatibility

        writer = csv.writer(response)
        writer.writerow(['级别', '题型', '难度', '题目', '选项A', '选项B', '选项C', '选项D', '选项E', '选项F', '答案', '解析', '来源'])

        TYPE_NAMES = {1: '单选题', 2: '多选题', 3: '判断题'}
        DIFF_NAMES = {1: '简单', 2: '中等', 3: '困难'}

        for q in qs:
            opts = q.options or []
            opt_map = {o['key']: o['text'] for o in opts}
            writer.writerow([
                f'{q.level_id}级',
                TYPE_NAMES.get(q.question_type, ''),
                DIFF_NAMES.get(q.difficulty, ''),
                q.content,
                opt_map.get('A', ''), opt_map.get('B', ''), opt_map.get('C', ''),
                opt_map.get('D', ''), opt_map.get('E', ''), opt_map.get('F', ''),
                q.answer,
                q.explanation or '',
                q.source or '',
            ])

        return response
    else:
        # JSON导出
        data = []
        for q in qs:
            data.append({
                'level': q.level_id,
                'question_type': q.question_type,
                'difficulty': q.difficulty,
                'content': q.content,
                'options': q.options,
                'answer': q.answer,
                'explanation': q.explanation or '',
                'source': q.source or '',
            })

        response = HttpResponse(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = 'attachment; filename="questions.json"'
        return response


@api_view(['GET'])
@permission_classes([AdminPermission])
def download_csv_template(request):
    """下载CSV导入模板"""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="import_template.csv"'
    response.write('\ufeff')  # BOM

    writer = csv.writer(response)
    writer.writerow(['级别', '题型', '难度', '题目', '选项A', '选项B', '选项C', '选项D', '选项E', '选项F', '答案', '解析', '来源'])
    # 写入示例行（展示代码标记语法）
    writer.writerow(['1级', '单选题', '简单', 'C++中，以下哪个是正确的输出语句？', 'print("hello")', 'cout<<"hello"', 'echo "hello"', 'printf "hello"', '', '', 'B', 'C++使用cout进行标准输出', '模拟题'])
    writer.writerow(['2级', '判断题', '中等', 'C++程序的执行从main函数开始。', '', '', '', '', '', '', 'T', '每个C++程序都必须有一个main函数', '模拟题'])
    writer.writerow(['3级', '多选题', '困难', '以下哪些是STL中的关联容器？', 'set', 'map', 'vector', 'unordered_map', '', '', 'ABD', 'set、map、unordered_map是关联容器', '模拟题'])
    writer.writerow(['1级', '单选题', '中等', '以下程序的输出是什么？```int a = 10, b = 3;\ncout << a / b;```', '3', '3.33', '10', '0', '', '', 'A', '整数除法向下取整', '模拟题'])
    writer.writerow(['2级', '单选题', '简单', '下面代码编译会报错，`int a, b; a=3，b = 4; cout << a;` 可能的原因是？', '中文逗号', '缺分号', '变量未定义', '语法错误', '', '', 'A', '中文逗号是无效字符', '模拟题'])

    return response


@api_view(['POST'])
@permission_classes([AdminPermission])
def batch_delete_questions(request):
    """批量删除题目"""
    ids = request.data.get('ids', [])
    if not ids:
        return Response({'detail': '请提供要删除的题目ID列表'}, status=400)

    deleted_count, _ = Question.objects.filter(id__in=ids).delete()
    return Response({
        'deleted_count': deleted_count,
    })
