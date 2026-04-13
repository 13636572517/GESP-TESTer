import random
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
        tqs = ExamTemplateQuestion.objects.filter(template=template).select_related('question')
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

        choice_ids = list(Question.objects.filter(
            level_id=level_id, is_active=True, question_type=1
        ).values_list('id', flat=True))
        judge_ids = list(Question.objects.filter(
            level_id=level_id, is_active=True, question_type=3
        ).values_list('id', flat=True))

        if not choice_ids and not judge_ids:
            return Response({'detail': '该级别暂无题目'}, status=400)

        actual_choice = min(CHOICE_COUNT, len(choice_ids))
        actual_judge = min(JUDGE_COUNT, len(judge_ids))

        if actual_choice == 0 and actual_judge == 0:
            return Response({'detail': '该级别暂无题目'}, status=400)

        selected_choice = random.sample(choice_ids, actual_choice) if actual_choice else []
        selected_judge = random.sample(judge_ids, actual_judge) if actual_judge else []

        # 先选择题，再判断题
        selected = selected_choice + selected_judge
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

    answers = record.answers.select_related('question').all()
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

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ExamTemplateCreateSerializer
        return ExamTemplateSerializer

    def get_queryset(self):
        return ExamTemplate.objects.select_related('level').all()


class AdminExamTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExamTemplate.objects.all()
    serializer_class = ExamTemplateSerializer
    permission_classes = [AdminPermission]
