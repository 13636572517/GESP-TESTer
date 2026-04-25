import csv
import io
import json
import random
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ExamTemplate, ExamTemplateQuestion, ExamRecord, ExamAnswer
from .serializers import (
    ExamTemplateSerializer, ExamTemplateCreateSerializer,
    ExamRecordSerializer, ExamAnswerSerializer, SaveAnswerSerializer,
)
from apps.questions.models import Question
from apps.questions.serializers import QuestionBriefSerializer
from apps.practice.views import update_stats_on_answer, check_answer
from apps.stats.models import DailyStudyLog


class ExamTemplateListView(generics.ListAPIView):
    serializer_class = ExamTemplateSerializer
    pagination_class = None

    def get_queryset(self):
        qs = ExamTemplate.objects.filter(is_active=True).select_related('level')
        level = self.request.query_params.get('level')
        if level:
            qs = qs.filter(level_id=level)
        return qs


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_exam(request):
    """开始考试"""
    template_id = request.data.get('template_id')
    level_id = request.data.get('level_id')
    exam_type = request.data.get('exam_type', 1)

    # 检查是否有进行中的考试
    ongoing = ExamRecord.objects.filter(user=request.user, status=0).first()
    if ongoing:
        # 返回进行中的考试
        return Response({
            'record_id': ongoing.id,
            'detail': '您有一场进行中的考试',
            'resume': True,
        })

    if exam_type == 1 and template_id:
        # 真题模拟
        try:
            template = ExamTemplate.objects.get(id=template_id, is_active=True)
        except ExamTemplate.DoesNotExist:
            return Response({'detail': '试卷不存在'}, status=404)

        record = ExamRecord.objects.create(
            user=request.user,
            template=template,
            level=template.level,
            exam_type=1,
            duration=template.duration,
            start_time=timezone.now(),
            total_score=template.total_score,
        )

        # 按模板生成答题记录
        tqs = ExamTemplateQuestion.objects.filter(template=template).order_by('sort_order').select_related('question')
        for tq in tqs:
            ExamAnswer.objects.create(
                record=record,
                question=tq.question,
                score=0,
            )

    elif exam_type == 2 and level_id:
        # 随机组卷：固定15道选择题 + 10道判断题，先选择后判断
        CHOICE_COUNT = 15
        JUDGE_COUNT = 10
        DURATION = 60

        # question_source: 1=真题库, 2=AI题库, 不传=全部
        question_source = request.data.get('question_source')
        base_filter = {'level_id': level_id, 'is_active': True}
        if question_source:
            base_filter['source_type'] = int(question_source)

        choice_ids = list(Question.objects.filter(
            **base_filter, question_type=1
        ).values_list('id', flat=True))
        judge_ids = list(Question.objects.filter(
            **base_filter, question_type=3
        ).values_list('id', flat=True))

        if not choice_ids and not judge_ids:
            return Response({'detail': '该级别暂无题目'}, status=400)

        actual_choice = min(CHOICE_COUNT, len(choice_ids))
        actual_judge = min(JUDGE_COUNT, len(judge_ids))

        if actual_choice == 0 and actual_judge == 0:
            return Response({'detail': '该级别暂无题目'}, status=400)

        selected_choice = sorted(random.sample(choice_ids, actual_choice)) if actual_choice else []
        selected_judge = sorted(random.sample(judge_ids, actual_judge)) if actual_judge else []

        # 先判断题，再选择题；同题型内题号小的优先
        selected = selected_judge + selected_choice
        total_count = len(selected)
        score_per_q = 100 // total_count if total_count else 0

        record = ExamRecord.objects.create(
            user=request.user,
            level_id=level_id,
            exam_type=2,
            duration=DURATION,
            start_time=timezone.now(),
            total_score=score_per_q * total_count,
        )

        for qid in selected:
            ExamAnswer.objects.create(
                record=record,
                question_id=qid,
                score=0,
            )
    else:
        return Response({'detail': '参数错误'}, status=400)

    # 获取考试题目
    answers = record.answers.select_related('question').all()
    questions = [a.question for a in answers]

    return Response({
        'record_id': record.id,
        'duration': record.duration,
        'total_score': record.total_score,
        'start_time': record.start_time,
        'questions': QuestionBriefSerializer(questions, many=True).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_exam(request, record_id):
    """获取考试信息（恢复考试时使用）"""
    try:
        record = ExamRecord.objects.get(id=record_id, user=request.user)
    except ExamRecord.DoesNotExist:
        return Response({'detail': '考试记录不存在'}, status=404)

    answers = record.answers.select_related('question').order_by('id')
    questions = [a.question for a in answers]

    # 已保存的答案
    saved_answers = {
        a.question_id: a.user_answer for a in answers if a.user_answer
    }

    return Response({
        'record_id': record.id,
        'duration': record.duration,
        'total_score': record.total_score,
        'start_time': record.start_time,
        'status': record.status,
        'questions': QuestionBriefSerializer(questions, many=True).data,
        'saved_answers': saved_answers,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_answer(request, record_id):
    """保存/更新答案（实时保存）"""
    try:
        record = ExamRecord.objects.get(id=record_id, user=request.user, status=0)
    except ExamRecord.DoesNotExist:
        return Response({'detail': '考试已结束或不存在'}, status=400)

    serializer = SaveAnswerSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        answer = ExamAnswer.objects.get(record=record, question_id=data['question_id'])
    except ExamAnswer.DoesNotExist:
        return Response({'detail': '题目不在本次考试中'}, status=400)

    answer.user_answer = data['user_answer']
    answer.time_spent = data['time_spent']
    answer.save(update_fields=['user_answer', 'time_spent'])

    return Response({'detail': '已保存'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_exam(request, record_id):
    """交卷"""
    try:
        record = ExamRecord.objects.get(id=record_id, user=request.user, status=0)
    except ExamRecord.DoesNotExist:
        return Response({'detail': '考试已结束或不存在'}, status=400)

    auto = request.data.get('auto', False)  # 是否自动交卷

    # 判分
    answers = record.answers.select_related('question').all()

    # 获取每道题的分值
    if record.template:
        score_map = dict(
            ExamTemplateQuestion.objects.filter(template=record.template)
            .values_list('question_id', 'score')
        )
    else:
        total_q = answers.count()
        default_score = record.total_score // total_q if total_q else 0
        score_map = {a.question_id: default_score for a in answers}

    earned = 0
    for answer in answers:
        is_correct = check_answer(answer.user_answer, answer.question.answer) if answer.user_answer else False
        q_score = score_map.get(answer.question_id, 0)
        answer.is_correct = is_correct
        answer.score = q_score if is_correct else 0
        answer.save()
        earned += answer.score

        update_stats_on_answer(request.user, answer.question, is_correct, answer.user_answer or '')

    record.earned_score = earned
    record.end_time = timezone.now()
    record.status = 2 if auto else 1
    record.save()

    # 更新每日学习记录
    today = timezone.localdate()
    log, _ = DailyStudyLog.objects.get_or_create(user=request.user, study_date=today)
    log.exam_count += 1
    log.save()

    return Response(ExamRecordSerializer(record).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_switch(request, record_id):
    """上报切屏事件"""
    try:
        record = ExamRecord.objects.get(id=record_id, user=request.user, status=0)
    except ExamRecord.DoesNotExist:
        return Response({'detail': '考试不存在'}, status=400)

    record.switch_count += 1
    record.save(update_fields=['switch_count'])
    return Response({'switch_count': record.switch_count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exam_result(request, record_id):
    """获取考试结果"""
    try:
        record = ExamRecord.objects.get(id=record_id, user=request.user)
    except ExamRecord.DoesNotExist:
        return Response({'detail': '考试记录不存在'}, status=404)

    if record.status == 0:
        return Response({'detail': '考试尚未结束'}, status=400)

    answers = record.answers.select_related('question__level').all()
    return Response({
        'record': ExamRecordSerializer(record).data,
        'answers': ExamAnswerSerializer(answers, many=True).data,
        'passed': record.earned_score >= (record.template.pass_score if record.template else (record.total_score * 60 // 100)),
    })


class ExamHistoryView(generics.ListAPIView):
    serializer_class = ExamRecordSerializer

    def get_queryset(self):
        return ExamRecord.objects.filter(
            user=self.request.user
        ).exclude(status=0).select_related('level', 'template').order_by('-created_at')


# --- 管理端 ---
from apps.questions.views import AdminPermission


class AdminExamTemplateListCreateView(generics.ListCreateAPIView):
    permission_classes = [AdminPermission]
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ExamTemplateCreateSerializer
        return ExamTemplateSerializer

    def get_queryset(self):
        qs = ExamTemplate.objects.select_related('level').all()
        level = self.request.query_params.get('level')
        if level:
            qs = qs.filter(level_id=level)
        return qs


class AdminExamTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExamTemplate.objects.all()
    permission_classes = [AdminPermission]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ExamTemplateCreateSerializer
        return ExamTemplateSerializer

    def retrieve(self, request, *args, **kwargs):
        from apps.questions.serializers import QuestionForExamSerializer
        instance = self.get_object()
        data = ExamTemplateSerializer(instance).data
        tqs = instance.template_questions.order_by('sort_order').select_related('question__level')
        questions = []
        for tq in tqs:
            q_data = dict(QuestionForExamSerializer(tq.question).data)
            q_data['score'] = tq.score
            q_data['sort_order'] = tq.sort_order
            questions.append(q_data)
        data['question_items'] = questions
        return Response(data)


@api_view(['GET'])
@permission_classes([AdminPermission])
def export_exam_templates(request):
    """导出试卷模板为CSV"""
    ids = request.query_params.get('ids', '')
    qs = ExamTemplate.objects.prefetch_related('template_questions__question').select_related('level')
    if ids:
        id_list = [int(i) for i in ids.split(',') if i.strip().isdigit()]
        qs = qs.filter(id__in=id_list)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'name', 'level_id', 'template_type', 'duration', 'total_score', 'pass_score', 'question_id', 'score', 'order'])

    for t in qs:
        tqs = list(t.template_questions.all().order_by('sort_order'))
        if not tqs:
            writer.writerow([t.id, t.name, t.level_id, t.template_type, t.duration, t.total_score, t.pass_score, '', '', ''])
        for tq in tqs:
            writer.writerow([t.id, t.name, t.level_id, t.template_type, t.duration, t.total_score, t.pass_score, tq.question_id, tq.score, tq.sort_order])

    response = HttpResponse(
        '\ufeff' + output.getvalue(),
        content_type='text/csv; charset=utf-8',
    )
    response['Content-Disposition'] = 'attachment; filename="exam_templates.csv"'
    return response


@api_view(['POST'])
@permission_classes([AdminPermission])
def import_exam_templates(request):
    """从CSV文件导入试卷模板"""
    file = request.FILES.get('file')
    if not file:
        return Response({'detail': '请上传CSV文件'}, status=400)

    try:
        reader = csv.DictReader(io.TextIOWrapper(file, encoding='utf-8-sig'))
        rows = list(reader)
    except Exception as e:
        return Response({'detail': f'文件解析失败: {e}'}, status=400)

    # 按 id（有则用）或 name+level_id 分组
    from collections import OrderedDict
    templates_map = OrderedDict()
    for row in rows:
        key = row.get('id') or f"{row.get('name')}_{row.get('level_id')}"
        if key not in templates_map:
            templates_map[key] = {
                'id': row.get('id', '').strip(),
                'name': row.get('name', '').strip(),
                'level_id': row.get('level_id', '').strip(),
                'template_type': row.get('template_type', '1').strip(),
                'duration': row.get('duration', '90').strip(),
                'total_score': row.get('total_score', '100').strip(),
                'pass_score': row.get('pass_score', '60').strip(),
                'questions': [],
            }
        qid = row.get('question_id', '').strip()
        if qid:
            templates_map[key]['questions'].append({
                'question_id': qid,
                'score': row.get('score', '2').strip(),
                'order': row.get('order', '0').strip(),
            })

    created_count = 0
    updated_count = 0
    errors = []
    for i, item in enumerate(templates_map.values()):
        try:
            t_id = item['id']
            existing = None
            if t_id:
                try:
                    existing = ExamTemplate.objects.get(pk=int(t_id))
                except ExamTemplate.DoesNotExist:
                    existing = None

            fields = dict(
                name=item['name'],
                level_id=int(item['level_id']),
                template_type=int(item.get('template_type') or 1),
                duration=int(item.get('duration') or 90),
                total_score=int(item.get('total_score') or 100),
                pass_score=int(item.get('pass_score') or 60),
            )
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                existing.save()
                existing.template_questions.all().delete()
                t = existing
                updated_count += 1
            else:
                # 若 CSV 指定了 ID，强制使用该 ID 以保持跨库导入的关联一致性
                if t_id:
                    fields['id'] = int(t_id)
                t = ExamTemplate.objects.create(**fields)
                created_count += 1

            q_ids = [int(q['question_id']) for q in item['questions'] if q['question_id']]
            valid_q_ids = set(Question.objects.filter(id__in=q_ids).values_list('id', flat=True))
            for q in item['questions']:
                qid = int(q['question_id'])
                if qid in valid_q_ids:
                    ExamTemplateQuestion.objects.create(
                        template=t,
                        question_id=qid,
                        score=int(q.get('score') or 2),
                        sort_order=int(q.get('order') or 0),
                    )
        except Exception as e:
            errors.append({'index': i + 1, 'name': item.get('name', ''), 'error': str(e)})

    return Response({'created_count': created_count, 'updated_count': updated_count, 'error_count': len(errors), 'errors': errors})
