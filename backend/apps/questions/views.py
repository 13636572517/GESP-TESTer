import csv
import io
import json
import re
from html import escape as html_escape
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, status, filters
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Question, QuestionFeedback
from .serializers import QuestionSerializer, QuestionCreateSerializer, QuestionForExamSerializer


class AdminQuestionPagination(PageNumberPagination):
    """管理端题目分页：允许客户端通过 page_size 参数控制每页数量"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 5000


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
    pagination_class = AdminQuestionPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content']
    ordering_fields = ['created_at', 'difficulty']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return QuestionCreateSerializer
        if self.request.query_params.get('for_exam'):
            return QuestionForExamSerializer
        return QuestionSerializer

    def get_queryset(self):
        for_exam = self.request.query_params.get('for_exam')
        if for_exam:
            # 组卷模式：只查必要字段，过滤禁用题，命中 (level_id, is_active) 索引
            qs = Question.objects.filter(is_active=True).only(
                'id', 'question_type', 'content', 'options', 'source'
            ).order_by('id')   # 主键天然有索引，避免 filesort
        else:
            # 管理列表：需要 level name 和 knowledge_points
            qs = Question.objects.select_related('level').prefetch_related('knowledge_points')

        level      = self.request.query_params.get('level')
        qtype      = self.request.query_params.get('type')
        difficulty = self.request.query_params.get('difficulty')
        knowledge  = self.request.query_params.get('knowledge')
        search     = self.request.query_params.get('search')
        source     = self.request.query_params.get('source')

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
        if source:
            qs = qs.filter(source__icontains=source)
        return qs

    def list(self, request, *args, **kwargs):
        # 组卷模式：跳过分页（不执行 COUNT(*)），直接返回数组
        if request.query_params.get('for_exam'):
            qs = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(qs, many=True)
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)


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
    updated = []
    errors = []
    for i, q_data in enumerate(questions_data):
        q_data = dict(q_data)
        q_id = q_data.pop('id', None)
        existing = None
        if q_id:
            try:
                existing = Question.objects.get(pk=int(q_id))
            except (Question.DoesNotExist, ValueError):
                existing = None

        if existing:
            serializer = QuestionCreateSerializer(existing, data=q_data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                updated.append(serializer.data)
            else:
                errors.append({'index': i, 'errors': serializer.errors})
        else:
            serializer = QuestionCreateSerializer(data=q_data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                created.append(serializer.data)
            else:
                errors.append({'index': i, 'errors': serializer.errors})

    return Response({
        'created_count': len(created),
        'updated_count': len(updated),
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
    updated = []
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

            # 有ID则覆盖更新，否则新增
            q_id_raw = row.get('ID', row.get('id', '')).strip()
            existing = None
            if q_id_raw:
                try:
                    existing = Question.objects.get(pk=int(q_id_raw))
                except (Question.DoesNotExist, ValueError):
                    existing = None

            if existing:
                serializer = QuestionCreateSerializer(existing, data=q_data, context={'request': request})
                if serializer.is_valid():
                    q_obj = serializer.save()
                    updated.append(i)
                else:
                    errors.append({'row': i + 2, 'errors': serializer.errors})
                    continue
            else:
                serializer = QuestionCreateSerializer(data=q_data, context={'request': request})
                if serializer.is_valid():
                    q_obj = serializer.save()
                    created.append(i)
                else:
                    errors.append({'row': i + 2, 'errors': serializer.errors})
                    continue

            # 处理知识点关联（优先用ID列，其次用名称列）
            kp_ids_raw = row.get('知识点ID', row.get('knowledge_point_ids', '')).strip()
            if kp_ids_raw:
                from apps.knowledge.models import KnowledgePoint
                ids = [int(x) for x in kp_ids_raw.split(',') if x.strip().isdigit()]
                kps = KnowledgePoint.objects.filter(id__in=ids)
                q_obj.knowledge_points.set(kps)
        except Exception as e:
            errors.append({'row': i + 2, 'errors': str(e)})

    return Response({
        'created_count': len(created),
        'updated_count': len(updated),
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
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(['ID', '级别', '题型', '难度', '题目', '选项A', '选项B', '选项C', '选项D', '选项E', '选项F', '答案', '解析', '来源', '知识点ID', '知识点'])

        TYPE_NAMES = {1: '单选题', 2: '多选题', 3: '判断题'}
        DIFF_NAMES = {1: '简单', 2: '中等', 3: '困难'}

        for q in qs:
            opts = q.options or []
            opt_map = {o['key']: o['text'] for o in opts}
            kps = list(q.knowledge_points.all())
            writer.writerow([
                q.id,
                f'{q.level_id}级',
                TYPE_NAMES.get(q.question_type, ''),
                DIFF_NAMES.get(q.difficulty, ''),
                q.content,
                opt_map.get('A', ''), opt_map.get('B', ''), opt_map.get('C', ''),
                opt_map.get('D', ''), opt_map.get('E', ''), opt_map.get('F', ''),
                q.answer,
                q.explanation or '',
                q.source or '',
                ','.join(str(kp.id) for kp in kps),
                ','.join(kp.name for kp in kps),
            ])

        response = HttpResponse(buf.getvalue().encode('utf-8-sig'), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="questions.csv"'
        return response
    else:
        # JSON导出
        data = []
        for q in qs:
            kps = list(q.knowledge_points.all())
            data.append({
                'id': q.id,
                'level': q.level_id,
                'question_type': q.question_type,
                'difficulty': q.difficulty,
                'content': q.content,
                'options': q.options,
                'answer': q.answer,
                'explanation': q.explanation or '',
                'source': q.source or '',
                'knowledge_point_ids': [kp.id for kp in kps],
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
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['级别', '题型', '难度', '题目', '选项A', '选项B', '选项C', '选项D', '选项E', '选项F', '答案', '解析', '来源', '知识点ID'])
    writer.writerow(['1级', '单选题', '简单', 'C++中，以下哪个是正确的输出语句？', 'print("hello")', 'cout<<"hello"', 'echo "hello"', 'printf "hello"', '', '', 'B', 'C++使用cout进行标准输出', '模拟题', ''])
    writer.writerow(['2级', '判断题', '中等', 'C++程序的执行从main函数开始。', '', '', '', '', '', '', 'T', '每个C++程序都必须有一个main函数', '模拟题', ''])
    writer.writerow(['3级', '多选题', '困难', '以下哪些是STL中的关联容器？', 'set', 'map', 'vector', 'unordered_map', '', '', 'ABD', 'set、map、unordered_map是关联容器', '模拟题', ''])
    writer.writerow(['1级', '单选题', '中等', '以下程序的输出是什么？```int a = 10, b = 3; cout << a / b;```', '3', '3.33', '10', '0', '', '', 'A', '整数除法向下取整', '模拟题', ''])
    writer.writerow(['2级', '单选题', '简单', '代码 `int a, b; cout << a;` 中a的值是？', '随机', '0', '1', '编译错误', '', '', 'A', '未初始化变量的值不确定', '模拟题', ''])
    response = HttpResponse(buf.getvalue().encode('utf-8-sig'), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="import_template.csv"'
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


# ── PDF 题目提取 ──────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AdminPermission])
def pdf_extract(request):
    """
    上传 PDF → 调用 Qwen-VL 提取题目 → 返回预览 JSON（不写入数据库）
    form-data: file=<pdf>, level=<1-8>, source=<来源描述>
    """
    from .pdf_import import extract_from_pdf

    pdf_file = request.FILES.get('file')
    if not pdf_file:
        return Response({'detail': '请上传PDF文件'}, status=400)
    if not pdf_file.name.lower().endswith('.pdf'):
        return Response({'detail': '仅支持PDF格式'}, status=400)

    level_raw = request.data.get('level', '1')
    try:
        level = int(level_raw)
        if not 1 <= level <= 8:
            raise ValueError
    except (ValueError, TypeError):
        return Response({'detail': '级别必须为1-8之间的整数'}, status=400)

    source = request.data.get('source', '').strip() or f'PDF导入'

    try:
        pdf_bytes = pdf_file.read()
        result = extract_from_pdf(pdf_bytes, level, source)
        return Response(result)
    except ValueError as e:
        return Response({'detail': str(e)}, status=400)
    except Exception as e:
        return Response({'detail': f'提取失败: {str(e)}'}, status=500)


@api_view(['POST'])
@permission_classes([AdminPermission])
def pdf_import_confirm(request):
    """
    将预览确认后的题目批量写入数据库
    body: { questions: [...] }  格式同 batch_create_questions
    """
    questions_data = request.data.get('questions', [])
    if not questions_data:
        return Response({'detail': '题目列表不能为空'}, status=400)

    created, errors = [], []
    for i, q_data in enumerate(questions_data):
        serializer = QuestionCreateSerializer(data=q_data, context={'request': request})
        if serializer.is_valid():
            instance = serializer.save()
            created.append(instance.id)
        else:
            errors.append({'index': i, 'errors': serializer.errors})

    return Response({
        'created_count': len(created),
        'error_count': len(errors),
        'errors': errors,
    })


# ─── AI 功能端点 ─────────────────────────────────────

@api_view(['POST'])
@permission_classes([AdminPermission])
def ai_suggest_tags(request):
    """
    AI 批量建议知识点标签（只返回建议，不写库）。
    请求体：{ "question_ids": [1, 2, ...] }
    返回：{ results: [{ question_id, content, suggested_ids }], errors: [...] }
    """
    from .ai_service import suggest_tags_for_question
    from apps.knowledge.models import KnowledgePoint

    question_ids = request.data.get('question_ids', [])
    if not question_ids:
        return Response({'detail': '请提供 question_ids'}, status=400)

    questions = list(Question.objects.filter(id__in=question_ids).only('id', 'content', 'level_id'))
    if not questions:
        return Response({'detail': '未找到题目'}, status=404)

    # 加载所有级别的知识点，支持跨级标注
    kps = KnowledgePoint.objects.select_related('chapter__level').values(
        'id', 'name', 'description',
        'chapter__name', 'chapter__level_id', 'chapter__level__name',
    ).order_by('chapter__level_id', 'chapter__sort_order')

    kp_list_all = [
        {
            'id':          kp['id'],
            'name':        kp['name'],
            'description': kp['description'] or '',
            'chapter':     kp['chapter__name'],
            'level':       kp['chapter__level_id'],
            'level_name':  kp['chapter__level__name'] or f"GESP{kp['chapter__level_id']}级",
        }
        for kp in kps
    ]

    results, errors = [], []
    for q in questions:
        if not kp_list_all:
            errors.append({'question_id': q.id, 'error': '系统中尚无知识点，请先导入知识点'})
            continue
        try:
            suggested = suggest_tags_for_question(q.content, kp_list_all, q.level_id)
            results.append({
                'question_id':   q.id,
                'content':       q.content[:120],
                'suggested_ids': suggested,
            })
        except Exception as e:
            errors.append({'question_id': q.id, 'error': str(e)})

    return Response({'results': results, 'errors': errors})


@api_view(['POST'])
@permission_classes([AdminPermission])
def ai_confirm_tags(request):
    """
    保存人工确认后的知识点标签。
    请求体：[{ "question_id": 1, "knowledge_point_ids": [5, 12] }, ...]
    """
    items = request.data
    if not isinstance(items, list):
        return Response({'detail': '请求体应为数组'}, status=400)

    updated = 0
    for item in items:
        qid   = item.get('question_id')
        kpids = item.get('knowledge_point_ids', [])
        try:
            q = Question.objects.get(id=qid)
            q.knowledge_points.set(kpids)
            updated += 1
        except Question.DoesNotExist:
            pass

    return Response({'updated': updated})


@api_view(['POST'])
@permission_classes([AdminPermission])
def ai_generate_questions(request):
    """
    AI 生成题目草稿（不入库，由前端展示审核后再提交 batch create）。
    请求体：{ "knowledge_point_id": 5, "question_type": 1, "count": 5 }
    """
    from .ai_service import generate_questions
    from apps.knowledge.models import KnowledgePoint

    kp_id = request.data.get('knowledge_point_id')
    qtype = int(request.data.get('question_type', 1))
    count = min(int(request.data.get('count', 5)), 10)

    if not kp_id:
        return Response({'detail': '请提供 knowledge_point_id'}, status=400)

    try:
        kp = KnowledgePoint.objects.select_related('chapter__level').get(id=kp_id)
    except KnowledgePoint.DoesNotExist:
        return Response({'detail': '知识点不存在'}, status=404)

    examples = list(
        Question.objects.filter(
            knowledge_points=kp, is_active=True, question_type=qtype
        ).values('content', 'options', 'answer')[:5]
    )

    try:
        drafts = generate_questions(
            knowledge_point_name=kp.name,
            knowledge_point_desc=kp.description,
            chapter_name=kp.chapter.name,
            level_name=kp.chapter.level.name,
            question_type=qtype,
            count=count,
            examples=examples,
        )
    except Exception as e:
        return Response({'detail': f'AI 生成失败：{e}'}, status=500)

    for d in drafts:
        d['level'] = kp.chapter.level_id
        d['knowledge_point_ids'] = [kp_id]

    return Response({'questions': drafts, 'knowledge_point': kp.name})


# ─── AI 配置管理 ──────────────────────────────────────────

from .ai_service import AVAILABLE_MODELS


@api_view(['GET', 'PUT'])
@permission_classes([AdminPermission])
def ai_config_view(request):
    """获取或更新 AI 配置（API Key、模型）"""
    from .models import AIConfig
    from .ai_service import invalidate_config_cache

    from .ai_service import encrypt_api_key, decrypt_api_key

    env_key = getattr(settings, 'DASHSCOPE_API_KEY', '')

    if request.method == 'GET':
        cfg = AIConfig.objects.first()
        db_has_key = bool(cfg and cfg.api_key)

        if db_has_key:
            # 解密后只展示脱敏版本，绝不返回明文
            plain = decrypt_api_key(cfg.api_key)
            masked = plain[:8] + '****' + plain[-4:] if len(plain) > 12 else '****'
            key_source = 'db'
        elif env_key:
            masked = env_key[:8] + '****' + env_key[-4:] if len(env_key) > 12 else '****'
            key_source = 'env'
        else:
            masked = ''
            key_source = 'none'

        return Response({
            'has_key':        db_has_key or bool(env_key),
            'key_source':     key_source,   # 'db' | 'env' | 'none'
            'api_key_masked': masked,
            'tag_model':      cfg.tag_model if cfg else 'qwen-plus',
            'gen_model':      cfg.gen_model if cfg else 'qwen-plus',
            'pdf_model':      cfg.pdf_model if cfg else 'qwen-vl-max',
            'updated_at':     cfg.updated_at if cfg else None,
            'available_models': AVAILABLE_MODELS,
        })

    # PUT —— 保存时加密，原始明文不落库
    cfg, _ = AIConfig.objects.get_or_create(id=1)
    if 'api_key' in request.data:
        new_key = request.data.get('api_key', '').strip()
        if new_key and '****' not in new_key:
            cfg.api_key = encrypt_api_key(new_key)   # 加密后存储
        elif not new_key:
            cfg.api_key = ''   # 清除，回退到 .env
    cfg.tag_model  = request.data.get('tag_model', cfg.tag_model)
    cfg.gen_model  = request.data.get('gen_model', cfg.gen_model)
    cfg.pdf_model  = request.data.get('pdf_model', cfg.pdf_model)
    cfg.updated_by = request.user
    cfg.save()
    invalidate_config_cache()
    return Response({'detail': '配置已保存'})


@api_view(['POST'])
@permission_classes([AdminPermission])
def ai_test_model(request):
    """测试指定模型的可用性，返回响应时间和结果"""
    import time
    from .ai_service import _call_qwen
    from .models import AIUsageLog

    model = request.data.get('model', 'qwen-plus')
    try:
        t0  = time.time()
        txt = _call_qwen(
            [{"role": "user", "content": "请只回复：ok"}],
            temperature=0,
            model=model,
            operation=AIUsageLog.OP_TEST,
        )
        return Response({
            'success':    True,
            'model':      model,
            'response':   txt,
            'latency_ms': int((time.time() - t0) * 1000),
        })
    except Exception as e:
        return Response({
            'success': False,
            'model':   model,
            'error':   str(e),
        })


@api_view(['GET'])
@permission_classes([AdminPermission])
def ai_usage_stats(request):
    """AI 用量统计：总量 / 按操作 / 按模型 / 每日趋势 / 最近记录"""
    from .models import AIUsageLog

    days  = max(1, min(int(request.query_params.get('days', 30)), 365))
    since = timezone.now() - timedelta(days=days)
    qs    = AIUsageLog.objects.filter(created_at__gte=since)

    totals = qs.aggregate(
        total_calls    = Count('id'),
        success_calls  = Count('id', filter=Q(success=True)),
        total_tokens   = Sum('total_tokens'),
        prompt_tokens  = Sum('prompt_tokens'),
        completion_tokens = Sum('completion_tokens'),
        avg_latency_ms = Avg('latency_ms'),
    )

    by_operation = list(
        qs.values('operation')
          .annotate(calls=Count('id'), tokens=Sum('total_tokens'),
                    success=Count('id', filter=Q(success=True)))
          .order_by('operation')
    )
    op_names = dict(AIUsageLog.OPERATION_CHOICES)
    for item in by_operation:
        item['operation_name'] = op_names.get(item['operation'], '未知')

    by_model = list(
        qs.values('model')
          .annotate(calls=Count('id'), tokens=Sum('total_tokens'))
          .order_by('-calls')
    )

    daily = list(
        qs.filter(success=True)
          .annotate(date=TruncDate('created_at'))
          .values('date')
          .annotate(calls=Count('id'), tokens=Sum('total_tokens'))
          .order_by('date')
    )
    for d in daily:
        d['date'] = d['date'].strftime('%Y-%m-%d') if d['date'] else ''

    recent = list(
        AIUsageLog.objects.all()[:50]
        .values('id', 'operation', 'model',
                'prompt_tokens', 'completion_tokens', 'total_tokens',
                'success', 'latency_ms', 'error_msg', 'created_at')
    )
    for item in recent:
        item['operation_name'] = op_names.get(item['operation'], '未知')

    return Response({
        'days':         days,
        'totals':       totals,
        'by_operation': by_operation,
        'by_model':     by_model,
        'daily':        daily,
        'recent':       recent,
    })


# ─── 题目反馈 ─────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback(request, pk):
    """学员提交题目反馈"""
    try:
        question = Question.objects.get(pk=pk, is_active=True)
    except Question.DoesNotExist:
        return Response({'detail': '题目不存在'}, status=404)

    feedback_type = request.data.get('feedback_type')
    content = request.data.get('content', '').strip()
    if not feedback_type:
        return Response({'detail': '请选择反馈类型'}, status=400)

    feedback = QuestionFeedback.objects.create(
        question=question,
        user=request.user,
        feedback_type=feedback_type,
        content=content,
    )
    return Response({'id': feedback.id, 'detail': '反馈已提交，感谢您的反馈！'}, status=201)


def _is_admin(request):
    return hasattr(request.user, 'profile') and request.user.profile.is_admin


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_feedback_list(request):
    """管理员：获取反馈列表"""
    if not _is_admin(request):
        return Response({'detail': '无权限'}, status=403)

    status_filter = request.query_params.get('status')
    qs = QuestionFeedback.objects.select_related('question', 'user__profile').order_by('-created_at')
    if status_filter is not None and status_filter != '':
        qs = qs.filter(status=status_filter)

    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    total = qs.count()
    items = qs[(page - 1) * page_size: page * page_size]

    data = []
    for fb in items:
        data.append({
            'id': fb.id,
            'question_id': fb.question_id,
            'question_content': fb.question.content[:80],
            'feedback_type': fb.feedback_type,
            'feedback_type_display': fb.get_feedback_type_display(),
            'content': fb.content,
            'status': fb.status,
            'status_display': fb.get_status_display(),
            'admin_reply': fb.admin_reply,
            'user_nickname': getattr(fb.user.profile, 'nickname', fb.user.username),
            'user_phone': getattr(fb.user.profile, 'phone', ''),
            'created_at': fb.created_at.strftime('%Y-%m-%d %H:%M'),
            'handled_at': fb.handled_at.strftime('%Y-%m-%d %H:%M') if fb.handled_at else None,
        })
    return Response({'count': total, 'results': data})


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def admin_feedback_handle(request, pk):
    """管理员：处理反馈（更新状态/回复）"""
    if not _is_admin(request):
        return Response({'detail': '无权限'}, status=403)

    try:
        feedback = QuestionFeedback.objects.get(pk=pk)
    except QuestionFeedback.DoesNotExist:
        return Response({'detail': '反馈不存在'}, status=404)

    new_status = request.data.get('status')
    admin_reply = request.data.get('admin_reply')

    if new_status is not None:
        feedback.status = new_status
        if int(new_status) in (QuestionFeedback.STATUS_HANDLED, QuestionFeedback.STATUS_IGNORED):
            from django.utils import timezone as tz
            feedback.handled_at = tz.now()
    if admin_reply is not None:
        feedback.admin_reply = admin_reply
    feedback.save()

    return Response({'detail': '已更新'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_feedbacks(request):
    """学员：获取自己的反馈列表"""
    qs = QuestionFeedback.objects.filter(user=request.user).select_related('question').order_by('-created_at')
    data = []
    for fb in qs:
        data.append({
            'id': fb.id,
            'question_id': fb.question_id,
            'question_content': fb.question.content[:100],
            'feedback_type': fb.feedback_type,
            'feedback_type_display': fb.get_feedback_type_display(),
            'content': fb.content,
            'status': fb.status,
            'status_display': fb.get_status_display(),
            'admin_reply': fb.admin_reply,
            'created_at': fb.created_at.strftime('%Y-%m-%d %H:%M'),
            'handled_at': fb.handled_at.strftime('%Y-%m-%d %H:%M') if fb.handled_at else None,
        })
    return Response({'results': data})
