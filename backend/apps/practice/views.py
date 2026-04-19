import random
from django.utils import timezone
from django.db.models import Count
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import PracticeSession, PracticeAnswer, MistakeRecord
from .serializers import (
    StartPracticeSerializer, SubmitAnswerSerializer,
    PracticeSessionSerializer, PracticeAnswerSerializer,
    MistakeRecordSerializer,
)
from apps.questions.models import Question
from apps.questions.serializers import QuestionBriefSerializer
from apps.stats.models import UserKnowledgeMastery, DailyStudyLog


def check_answer(user_answer, correct_answer):
    """比较答案，多选题忽略顺序（如 BA == AB）"""
    return sorted(user_answer.upper()) == sorted(correct_answer.upper())


def update_stats_on_answer(user, question, is_correct, user_answer=''):
    """答题后更新统计数据"""
    # 更新知识点掌握度
    for kp in question.knowledge_points.all():
        mastery, _ = UserKnowledgeMastery.objects.get_or_create(
            user=user, knowledge=kp
        )
        mastery.total_attempts += 1
        if is_correct:
            mastery.correct_count += 1
        mastery.last_practiced = timezone.now()
        mastery.update_mastery()
        mastery.save()

    # 更新错题本
    if not is_correct:
        mistake, created = MistakeRecord.objects.get_or_create(
            user=user, question=question
        )
        if not created:
            mistake.wrong_count += 1
        mistake.consecutive_correct = 0
        mistake.is_mastered = False
        mistake.last_wrong_answer = user_answer
        mistake.last_practiced_at = timezone.now()
        mistake.save()
    else:
        # 答对了，更新连续正确次数
        try:
            mistake = MistakeRecord.objects.get(user=user, question=question)
            mistake.consecutive_correct += 1
            mistake.last_practiced_at = timezone.now()
            if mistake.consecutive_correct >= 3:
                mistake.is_mastered = True
            mistake.save()
        except MistakeRecord.DoesNotExist:
            pass

    # 更新每日学习记录
    today = timezone.localdate()
    log, _ = DailyStudyLog.objects.get_or_create(user=user, study_date=today)
    log.practice_count += 1
    if is_correct:
        log.correct_count += 1
    log.save()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_practice(request):
    serializer = StartPracticeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    session_type = data['session_type']
    count = data['count']
    qs = Question.objects.filter(is_active=True)

    if session_type == 1:  # 知识点专练
        knowledge_ids = data.get('knowledge_ids', [])
        if knowledge_ids:
            qs = qs.filter(knowledge_points__id__in=knowledge_ids).distinct()
        if data.get('level_id'):
            qs = qs.filter(level_id=data['level_id'])
    elif session_type == 2:  # 随机组题
        if data.get('level_id'):
            qs = qs.filter(level_id=data['level_id'])
        if data.get('difficulty'):
            qs = qs.filter(difficulty=data['difficulty'])
    elif session_type == 3:  # 错题复习
        mistake_qids = MistakeRecord.objects.filter(
            user=request.user, is_mastered=False
        ).values_list('question_id', flat=True)
        qs = qs.filter(id__in=mistake_qids)

    # 随机选取题目
    question_ids = list(qs.values_list('id', flat=True))
    if len(question_ids) > count:
        question_ids = random.sample(question_ids, count)

    if not question_ids:
        return Response({'detail': '没有符合条件的题目'}, status=400)

    session = PracticeSession.objects.create(
        user=request.user,
        session_type=session_type,
        level_id=data.get('level_id'),
        total_count=len(question_ids),
    )

    # 创建答题记录(预生成)
    questions = Question.objects.filter(id__in=question_ids)
    for q in questions:
        PracticeAnswer.objects.create(session=session, question=q)

    return Response({
        'session_id': session.id,
        'questions': QuestionBriefSerializer(questions, many=True).data,
        'total_count': len(question_ids),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request, session_id):
    try:
        session = PracticeSession.objects.get(id=session_id, user=request.user)
    except PracticeSession.DoesNotExist:
        return Response({'detail': '练习记录不存在'}, status=404)

    if session.finished_at:
        return Response({'detail': '练习已结束'}, status=400)

    serializer = SubmitAnswerSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        answer = PracticeAnswer.objects.get(
            session=session, question_id=data['question_id']
        )
    except PracticeAnswer.DoesNotExist:
        return Response({'detail': '题目不在本次练习中'}, status=400)

    question = answer.question
    is_correct = check_answer(data['user_answer'], question.answer)

    answer.user_answer = data['user_answer']
    answer.is_correct = is_correct
    answer.time_spent = data['time_spent']
    answer.save()

    if is_correct:
        session.correct_count = session.answers.filter(is_correct=True).count()
        session.save(update_fields=['correct_count'])

    update_stats_on_answer(request.user, question, is_correct, data['user_answer'])

    return Response({
        'is_correct': is_correct,
        'correct_answer': question.answer,
        'explanation': question.explanation,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finish_practice(request, session_id):
    try:
        session = PracticeSession.objects.get(id=session_id, user=request.user)
    except PracticeSession.DoesNotExist:
        return Response({'detail': '练习记录不存在'}, status=404)

    session.correct_count = session.answers.filter(is_correct=True).count()
    session.finished_at = timezone.now()
    session.save()

    answers = session.answers.select_related('question').all()
    return Response({
        'total_count': session.total_count,
        'correct_count': session.correct_count,
        'accuracy': round(session.correct_count / session.total_count * 100, 1) if session.total_count else 0,
        'answers': PracticeAnswerSerializer(answers, many=True).data,
    })


class PracticeHistoryView(generics.ListAPIView):
    serializer_class = PracticeSessionSerializer

    def get_queryset(self):
        return PracticeSession.objects.filter(
            user=self.request.user, finished_at__isnull=False
        ).order_by('-created_at')


# --- 错题本 ---

class MistakeListView(generics.ListAPIView):
    serializer_class = MistakeRecordSerializer

    def get_queryset(self):
        qs = MistakeRecord.objects.filter(user=self.request.user).select_related(
            'question__level'
        )
        level = self.request.query_params.get('level')
        mastered = self.request.query_params.get('mastered')
        knowledge = self.request.query_params.get('knowledge')

        if level:
            qs = qs.filter(question__level_id=level)
        if mastered is not None:
            qs = qs.filter(is_mastered=mastered == 'true')
        if knowledge:
            qs = qs.filter(question__knowledge_points__id=knowledge)
        return qs.order_by('-wrong_count')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mistake_stats(request):
    """错题统计（按知识点聚合）"""
    stats = MistakeRecord.objects.filter(
        user=request.user, is_mastered=False
    ).values(
        'question__knowledge_points__id',
        'question__knowledge_points__name',
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    return Response([
        {
            'knowledge_id': s['question__knowledge_points__id'],
            'knowledge_name': s['question__knowledge_points__name'],
            'mistake_count': s['count'],
        }
        for s in stats if s['question__knowledge_points__id']
    ])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mistake_review(request):
    """生成错题复习卷"""
    count = request.data.get('count', 20)
    mistake_qids = list(MistakeRecord.objects.filter(
        user=request.user, is_mastered=False
    ).order_by('-wrong_count', 'last_practiced_at').values_list('question_id', flat=True))

    if not mistake_qids:
        return Response({'detail': '暂无错题'}, status=400)

    # 优先取错误次数多、长时间未复习的题
    selected = mistake_qids[:count]
    questions = Question.objects.filter(id__in=selected)

    session = PracticeSession.objects.create(
        user=request.user,
        session_type=3,
        total_count=len(selected),
    )
    for q in questions:
        PracticeAnswer.objects.create(session=session, question=q)

    return Response({
        'session_id': session.id,
        'questions': QuestionBriefSerializer(questions, many=True).data,
        'total_count': len(selected),
    })


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def mark_mastered(request, pk):
    try:
        mistake = MistakeRecord.objects.get(id=pk, user=request.user)
    except MistakeRecord.DoesNotExist:
        return Response({'detail': '记录不存在'}, status=404)
    mistake.is_mastered = True
    mistake.save(update_fields=['is_mastered'])
    return Response({'detail': '已标记为掌握'})


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def unmark_mastered(request, pk):
    try:
        mistake = MistakeRecord.objects.get(id=pk, user=request.user)
    except MistakeRecord.DoesNotExist:
        return Response({'detail': '记录不存在'}, status=404)
    mistake.is_mastered = False
    mistake.save(update_fields=['is_mastered'])
    return Response({'detail': '已撤销掌握'})
