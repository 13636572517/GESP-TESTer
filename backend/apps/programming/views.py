import base64
import requests
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import generics
from .models import ProgrammingQuestion, TestCase, CodeSubmission


JUDGE0_URL = getattr(settings, 'JUDGE0_URL', 'http://localhost:2358')

JUDGE0_STATUS_MAP = {
    1: CodeSubmission.STATUS_PENDING,
    2: CodeSubmission.STATUS_RUNNING,
    3: CodeSubmission.STATUS_ACCEPTED,
    4: CodeSubmission.STATUS_WRONG,
    5: CodeSubmission.STATUS_TLE,
    6: CodeSubmission.STATUS_CE,
    7: CodeSubmission.STATUS_RE,
    8: CodeSubmission.STATUS_RE,
    9: CodeSubmission.STATUS_RE,
    10: CodeSubmission.STATUS_RE,
    11: CodeSubmission.STATUS_RE,
    12: CodeSubmission.STATUS_RE,
    13: CodeSubmission.STATUS_ERROR,
    14: CodeSubmission.STATUS_RE,
}


def _serialize_question(q, detail=False):
    data = {
        'id': q.id,
        'title': q.title,
        'difficulty': q.difficulty,
        'difficulty_display': q.get_difficulty_display(),
        'level_id': q.level_id,
        'time_limit': q.time_limit,
        'memory_limit': q.memory_limit,
    }
    if detail:
        data['description'] = q.description
        data['input_description'] = q.input_description
        data['output_description'] = q.output_description
        data['samples'] = [
            {'input': tc.input_data, 'output': tc.expected_output}
            for tc in q.test_cases.filter(is_sample=True)
        ]
        data['accepted_count'] = q.submissions.filter(status=CodeSubmission.STATUS_ACCEPTED).values('user').distinct().count()
        data['submit_count'] = q.submissions.values('user').distinct().count()
    return data


# ── 学员接口 ──────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def question_list(request):
    qs = ProgrammingQuestion.objects.filter(is_active=True).select_related('level')
    level_id = request.query_params.get('level')
    if level_id:
        qs = qs.filter(level_id=level_id)
    return Response([_serialize_question(q) for q in qs])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def question_detail(request, pk):
    try:
        q = ProgrammingQuestion.objects.get(pk=pk, is_active=True)
    except ProgrammingQuestion.DoesNotExist:
        return Response({'detail': '题目不存在'}, status=404)
    return Response(_serialize_question(q, detail=True))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_code(request, pk):
    try:
        question = ProgrammingQuestion.objects.prefetch_related('test_cases').get(pk=pk, is_active=True)
    except ProgrammingQuestion.DoesNotExist:
        return Response({'detail': '题目不存在'}, status=404)

    code = request.data.get('code', '').strip()
    language_id = int(request.data.get('language_id', CodeSubmission.LANGUAGE_CPP))

    if not code:
        return Response({'detail': '代码不能为空'}, status=400)

    test_cases = list(question.test_cases.all())
    if not test_cases:
        return Response({'detail': '题目暂无测试点'}, status=400)

    submission = CodeSubmission.objects.create(
        question=question,
        user=request.user,
        code=code,
        language_id=language_id,
        status=CodeSubmission.STATUS_RUNNING,
        total_cases=len(test_cases),
    )

    STATUS_LABEL = {
        CodeSubmission.STATUS_ACCEPTED: 'AC',
        CodeSubmission.STATUS_WRONG: 'WA',
        CodeSubmission.STATUS_TLE: 'TLE',
        CodeSubmission.STATUS_MLE: 'MLE',
        CodeSubmission.STATUS_RE: 'RE',
        CodeSubmission.STATUS_CE: 'CE',
        CodeSubmission.STATUS_ERROR: 'ERR',
    }

    passed = 0
    last_result = {}
    worst_status = CodeSubmission.STATUS_ACCEPTED
    case_results = []
    first_error = None

    for i, tc in enumerate(test_cases):
        def b64(s):
            return base64.b64encode(s.encode()).decode() if s else ''

        def decode(s):
            try:
                return base64.b64decode(s).decode('utf-8', errors='replace') if s else ''
            except Exception:
                return s or ''

        try:
            resp = requests.post(
                f'{JUDGE0_URL}/submissions?wait=true&base64_encoded=true',
                json={
                    'language_id': language_id,
                    'source_code': b64(code),
                    'stdin': b64(tc.input_data),
                    'expected_output': b64(tc.expected_output),
                    'cpu_time_limit': question.time_limit / 1000,
                    'memory_limit': question.memory_limit * 1024,
                },
                timeout=60,
                proxies={'http': None, 'https': None},
            )
            raw = resp.json()
            result = {
                **raw,
                'stdout': decode(raw.get('stdout')),
                'stderr': decode(raw.get('stderr')),
                'compile_output': decode(raw.get('compile_output')),
            }
        except Exception as e:
            first_error = str(e)
            submission.status = CodeSubmission.STATUS_ERROR
            submission.stderr = first_error
            submission.save()
            return Response({
                'id': submission.id,
                'status': submission.status,
                'status_display': submission.get_status_display(),
                'passed_cases': 0,
                'total_cases': len(test_cases),
                'time_used': None,
                'memory_used': None,
                'compile_output': '',
                'stderr': first_error,
                'case_results': [],
            })

        judge0_status = result.get('status', {}).get('id', 13)
        mapped = JUDGE0_STATUS_MAP.get(judge0_status, CodeSubmission.STATUS_ERROR)
        last_result = result

        case_results.append({
            'index': i + 1,
            'status': mapped,
            'label': STATUS_LABEL.get(mapped, 'ERR'),
            'time': result.get('time'),
            'memory': result.get('memory'),
        })

        if mapped == CodeSubmission.STATUS_ACCEPTED:
            passed += 1
        else:
            if worst_status == CodeSubmission.STATUS_ACCEPTED:
                worst_status = mapped
            if mapped == CodeSubmission.STATUS_CE:
                for j in range(i + 1, len(test_cases)):
                    case_results.append({'index': j + 1, 'status': CodeSubmission.STATUS_CE, 'label': 'CE', 'time': None, 'memory': None})
                break

    final_status = CodeSubmission.STATUS_ACCEPTED if passed == len(test_cases) else worst_status

    submission.status = final_status
    submission.passed_cases = passed
    submission.stdout = (last_result.get('stdout') or '')[:2000]
    submission.stderr = (last_result.get('stderr') or '')[:2000]
    submission.compile_output = (last_result.get('compile_output') or '')[:2000]
    submission.time_used = float(last_result.get('time') or 0)
    submission.memory_used = last_result.get('memory') or 0
    submission.save()

    return Response({
        'id': submission.id,
        'status': submission.status,
        'status_display': submission.get_status_display(),
        'passed_cases': passed,
        'total_cases': len(test_cases),
        'time_used': submission.time_used,
        'memory_used': submission.memory_used,
        'compile_output': submission.compile_output,
        'stderr': submission.stderr,
        'case_results': case_results,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_submissions(request, pk):
    subs = CodeSubmission.objects.filter(question_id=pk, user=request.user)[:10]
    return Response([{
        'id': s.id,
        'status': s.status,
        'status_display': s.get_status_display(),
        'passed_cases': s.passed_cases,
        'total_cases': s.total_cases,
        'time_used': s.time_used,
        'memory_used': s.memory_used,
        'created_at': s.created_at.strftime('%Y-%m-%d %H:%M'),
    } for s in subs])


# ── 管理员接口 ────────────────────────────────────────────────

def _is_admin(request):
    return hasattr(request.user, 'profile') and request.user.profile.is_admin


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def admin_question_list(request):
    if not _is_admin(request):
        return Response({'detail': '无权限'}, status=403)
    if request.method == 'GET':
        qs = ProgrammingQuestion.objects.select_related('level').all()
        return Response([_serialize_question(q) for q in qs])
    data = request.data
    q = ProgrammingQuestion.objects.create(
        level_id=data['level_id'],
        title=data['title'],
        description=data.get('description', ''),
        input_description=data.get('input_description', ''),
        output_description=data.get('output_description', ''),
        difficulty=data.get('difficulty', 1),
        time_limit=data.get('time_limit', 1000),
        memory_limit=data.get('memory_limit', 256),
        created_by=request.user,
    )
    return Response({'id': q.id}, status=201)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def admin_question_detail(request, pk):
    if not _is_admin(request):
        return Response({'detail': '无权限'}, status=403)
    try:
        q = ProgrammingQuestion.objects.get(pk=pk)
    except ProgrammingQuestion.DoesNotExist:
        return Response({'detail': '不存在'}, status=404)

    if request.method == 'GET':
        data = _serialize_question(q, detail=True)
        data['test_cases'] = [
            {'id': tc.id, 'input_data': tc.input_data, 'expected_output': tc.expected_output,
             'is_sample': tc.is_sample, 'order': tc.order}
            for tc in q.test_cases.all()
        ]
        return Response(data)

    if request.method == 'PUT':
        d = request.data
        for f in ['title', 'description', 'input_description', 'output_description',
                  'difficulty', 'time_limit', 'memory_limit', 'is_active']:
            if f in d:
                setattr(q, f, d[f])
        if 'level_id' in d:
            q.level_id = d['level_id']
        q.save()
        return Response({'detail': 'ok'})

    q.delete()
    return Response(status=204)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_test_cases(request, pk):
    if not _is_admin(request):
        return Response({'detail': '无权限'}, status=403)
    try:
        q = ProgrammingQuestion.objects.get(pk=pk)
    except ProgrammingQuestion.DoesNotExist:
        return Response({'detail': '不存在'}, status=404)

    cases = request.data.get('test_cases', [])
    q.test_cases.all().delete()
    for i, tc in enumerate(cases):
        TestCase.objects.create(
            question=q,
            input_data=tc.get('input_data', ''),
            expected_output=tc.get('expected_output', ''),
            is_sample=tc.get('is_sample', False),
            order=i,
        )
    return Response({'detail': 'ok', 'count': len(cases)})
