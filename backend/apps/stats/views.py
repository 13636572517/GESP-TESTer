from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import UserKnowledgeMastery, DailyStudyLog
from .serializers import MasterySerializer, DailyStudyLogSerializer
from apps.practice.models import PracticeSession, MistakeRecord


@api_view(['GET'])
def overview(request):
    """学习总览"""
    user = request.user
    logs = DailyStudyLog.objects.filter(user=user)
    totals = logs.aggregate(
        total_practice=Sum('practice_count'),
        total_correct=Sum('correct_count'),
        total_exams=Sum('exam_count'),
        total_minutes=Sum('study_minutes'),
    )

    study_days = logs.count()
    total_practice = totals['total_practice'] or 0
    total_correct = totals['total_correct'] or 0
    accuracy = round(total_correct / total_practice * 100, 1) if total_practice else 0

    mistake_count = MistakeRecord.objects.filter(user=user, is_mastered=False).count()

    return Response({
        'total_practice': total_practice,
        'total_correct': total_correct,
        'accuracy': accuracy,
        'total_exams': totals['total_exams'] or 0,
        'study_days': study_days,
        'study_minutes': totals['total_minutes'] or 0,
        'unmastered_mistakes': mistake_count,
    })


@api_view(['GET'])
def mastery(request):
    """知识点掌握度"""
    level = request.query_params.get('level')
    qs = UserKnowledgeMastery.objects.filter(user=request.user).select_related(
        'knowledge__chapter__level'
    )
    if level:
        qs = qs.filter(knowledge__chapter__level_id=level)

    return Response(MasterySerializer(qs, many=True).data)


@api_view(['GET'])
def daily_stats(request):
    """每日学习曲线"""
    days = int(request.query_params.get('days', 30))
    start_date = timezone.localdate() - timedelta(days=days)
    logs = DailyStudyLog.objects.filter(
        user=request.user, study_date__gte=start_date
    ).order_by('study_date')
    return Response(DailyStudyLogSerializer(logs, many=True).data)


@api_view(['GET'])
def weakness(request):
    """薄弱知识点分析"""
    weak = UserKnowledgeMastery.objects.filter(
        user=request.user,
        total_attempts__gte=3,
        mastery_level__lte=2,
    ).select_related('knowledge__chapter__level').order_by('mastery_level')[:10]

    return Response(MasterySerializer(weak, many=True).data)
