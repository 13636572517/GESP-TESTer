"""
普通用户的 AI 设置接口：
  GET/PUT  /user/ai-config/      获取或更新用户的 AI 配置（API Key、模型）
  POST     /user/ai-config/test/ 测试用户自己的模型连通性
  GET      /user/ai-usage/       用户自己的用量统计
  POST     /user/ai-explain/     题目 AI 讲解（SSE 流式输出）
"""
import json
import time
from datetime import timedelta

from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.questions.ai_service import (
    encrypt_api_key, decrypt_api_key,
    call_qwen_for_user, AVAILABLE_MODELS,
)
from .models import UserAIConfig


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_ai_config(request):
    """获取或更新当前用户的 AI 配置"""
    cfg, _ = UserAIConfig.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        if cfg.api_key:
            plain  = decrypt_api_key(cfg.api_key)
            masked = plain[:8] + '****' + plain[-4:] if len(plain) > 12 else '****'
            has_key = True
        else:
            masked  = ''
            has_key = False

        return Response({
            'has_key':          has_key,
            'api_key_masked':   masked,
            'tag_model':        cfg.tag_model,
            'gen_model':        cfg.gen_model,
            'updated_at':       cfg.updated_at,
            'available_models': AVAILABLE_MODELS,
        })

    # PUT
    if 'api_key' in request.data:
        new_key = request.data.get('api_key', '').strip()
        if new_key and '****' not in new_key:
            cfg.api_key = encrypt_api_key(new_key)
        elif not new_key:
            cfg.api_key = ''
    cfg.tag_model = request.data.get('tag_model', cfg.tag_model)
    cfg.gen_model = request.data.get('gen_model', cfg.gen_model)
    cfg.save()
    return Response({'detail': '配置已保存'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_ai_test(request):
    """测试用户自己的 API Key 是否可用"""
    from apps.questions.models import AIUsageLog
    model = request.data.get('model', 'qwen-plus')
    start = int(time.time() * 1000)
    try:
        resp = call_qwen_for_user(
            user=request.user,
            messages=[
                {'role': 'system', 'content': '你是一个助手。'},
                {'role': 'user',   'content': '请回复：OK'},
            ],
            temperature=0.1,
            model=model,
            operation=AIUsageLog.OP_TEST,
        )
        return Response({
            'success':    True,
            'latency_ms': int(time.time() * 1000) - start,
            'response':   resp[:200],
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_ai_usage(request):
    """当前用户的 AI 用量统计"""
    from apps.questions.models import AIUsageLog

    days = int(request.query_params.get('days', 30))
    since = timezone.now() - timedelta(days=days)
    qs = AIUsageLog.objects.filter(user=request.user, created_at__gte=since)

    # 汇总
    totals = qs.aggregate(
        total_calls=Count('id'),
        success_calls=Count('id', filter=Q(success=True)),
        total_tokens=Sum('total_tokens'),
        avg_latency_ms=Avg('latency_ms'),
    )

    # 按操作类型
    by_op = []
    for op_val, op_name in AIUsageLog.OPERATION_CHOICES:
        sub = qs.filter(operation=op_val).aggregate(
            calls=Count('id'),
            success=Count('id', filter=Q(success=True)),
            tokens=Sum('total_tokens'),
        )
        if sub['calls']:
            by_op.append({'operation_name': op_name, **sub})
    by_model = list(
        qs.values('model').annotate(calls=Count('id'), tokens=Sum('total_tokens')).order_by('-calls')
    )

    # 每日趋势
    daily = list(
        qs.annotate(date=TruncDate('created_at'))
          .values('date')
          .annotate(calls=Count('id'), tokens=Sum('total_tokens'))
          .order_by('date')
    )
    for d in daily:
        d['date'] = str(d['date'])

    # 最近50条
    recent = list(
        qs.order_by('-created_at')[:50].values(
            'created_at', 'operation', 'model',
            'success', 'total_tokens', 'latency_ms', 'error_msg',
        )
    )
    op_map = dict(AIUsageLog.OPERATION_CHOICES)
    for r in recent:
        r['operation_name'] = op_map.get(r['operation'], '')
        r['created_at'] = str(r['created_at'])

    return Response({
        'totals':       totals,
        'by_operation': by_op,
        'by_model':     by_model,
        'daily':        daily,
        'recent':       recent,
    })


# ─── AI 题目讲解（SSE 流式）─────────────────────────────────

from django.http import StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt


def _jwt_user(request):
    """从 Bearer token 中解析用户，返回 User 或 None"""
    from django.contrib.auth.models import User
    from rest_framework_simplejwt.authentication import JWTAuthentication
    try:
        auth = JWTAuthentication()
        result = auth.authenticate(request)
        return result[0] if result else None
    except Exception:
        return None


@csrf_exempt
def ai_explain_stream(request):
    """
    POST /user/ai-explain/
    Body: { question_id, user_answer, is_correct, messages: [{role, content}] }
    Response: SSE text/event-stream
      data: {"content": "..."}   — 增量文字
      data: [DONE]               — 结束
      data: {"error": "..."}     — 错误
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    user = _jwt_user(request)
    if not user:
        return HttpResponse(status=401)

    try:
        body        = json.loads(request.body)
        question_id = body.get('question_id')
        user_answer = body.get('user_answer', '')
        is_correct  = body.get('is_correct', False)
        history     = body.get('messages', [])   # [{role, content}, ...]
    except Exception:
        return HttpResponse(status=400)

    # 加载题目
    from apps.questions.models import Question, AIUsageLog
    try:
        q = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return HttpResponse(status=404)

    # 构建题目上下文
    options_text = ''
    if q.options:
        options_text = '\n'.join(f"  {o['key']}. {o['text']}" for o in q.options)
    question_ctx = (
        f"题目类型：{q.get_question_type_display()}\n"
        f"题目内容：{q.content}\n"
        + (f"选项：\n{options_text}\n" if options_text else '')
        + f"正确答案：{q.answer}\n"
        f"学生答案：{user_answer or '未作答'}\n"
        f"是否答对：{'是' if is_correct else '否'}\n"
        f"官方解析：{q.explanation or '（无）'}"
    )

    from apps.questions.ai_service import EXPLAIN_SYSTEM, _get_user_client, _get_user_model
    model = _get_user_model(user, 'gen')

    # 首次讲解 or 续聊
    system_msg = {'role': 'system', 'content': EXPLAIN_SYSTEM + '\n\n【本题信息】\n' + question_ctx}
    if not history:
        call_msgs = [system_msg, {'role': 'user', 'content': '请为我详细讲解这道题。'}]
    else:
        call_msgs = [system_msg] + history

    def sse(data):
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    def stream_gen():
        try:
            client = _get_user_client(user)
        except ValueError as e:
            yield sse({'error': str(e)})
            yield 'data: [DONE]\n\n'
            return

        start_ms = int(time.time() * 1000)
        success  = False
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=call_msgs,
                temperature=0.3,
                max_tokens=2048,
                stream=True,
            )
            for chunk in resp:
                delta = chunk.choices[0].delta.content or ''
                if delta:
                    yield sse({'content': delta})
            success = True
            yield 'data: [DONE]\n\n'
        except Exception as e:
            yield sse({'error': str(e)[:300]})
            yield 'data: [DONE]\n\n'
        finally:
            try:
                AIUsageLog.objects.create(
                    operation=AIUsageLog.OP_EXPLAIN, model=model,
                    prompt_tokens=0, completion_tokens=0, total_tokens=0,
                    success=success,
                    latency_ms=int(time.time() * 1000) - start_ms,
                    user=user,
                )
            except Exception:
                pass

    response = StreamingHttpResponse(stream_gen(), content_type='text/event-stream; charset=utf-8')
    response['Cache-Control']    = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
