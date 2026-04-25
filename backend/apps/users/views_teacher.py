from datetime import timedelta
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Classroom, ClassroomMember
from apps.exams.models import ExamRecord
from apps.stats.models import DailyStudyLog


class IsTeacherOrAdmin(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        p = getattr(request.user, 'profile', None)
        return p and (p.is_admin or p.is_teacher)


def _get_teacher_classroom(request, pk):
    """获取教师有权访问的班级，管理员可访问所有"""
    p = request.user.profile
    if p.is_admin:
        return Classroom.objects.select_related('level').get(pk=pk)
    return request.user.teaching_classrooms.select_related('level').get(pk=pk)


def _since(days_str):
    if days_str == 'all':
        return None
    try:
        return timezone.now() - timedelta(days=int(days_str))
    except (ValueError, TypeError):
        return timezone.now() - timedelta(days=30)


@api_view(['GET'])
@permission_classes([IsTeacherOrAdmin])
def teacher_classes(request):
    """老师的班级列表；管理员返回全部"""
    p = request.user.profile
    if p.is_admin:
        qs = Classroom.objects.select_related('level').prefetch_related('teachers__profile').all()
    else:
        qs = request.user.teaching_classrooms.select_related('level').prefetch_related('teachers__profile').all()

    result = []
    for c in qs:
        result.append({
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'level_name': c.level.name if c.level else '',
            'member_count': c.members.count(),
            'is_active': c.is_active,
        })
    return Response(result)


@api_view(['GET'])
@permission_classes([IsTeacherOrAdmin])
def teacher_class_overview(request, pk):
    """班级学情概览：每个学员的汇总统计"""
    try:
        classroom = _get_teacher_classroom(request, pk)
    except Classroom.DoesNotExist:
        return Response({'detail': '班级不存在或无权访问'}, status=404)

    days_str = request.query_params.get('days', '30')
    since = _since(days_str)

    members = ClassroomMember.objects.filter(
        classroom=classroom
    ).select_related('user__profile').order_by('joined_at')

    students = []
    for m in members:
        user = m.user
        p = getattr(user, 'profile', None)

        exam_qs = ExamRecord.objects.filter(user=user).exclude(status=0)
        if since:
            exam_qs = exam_qs.filter(created_at__gte=since)
        exam_agg = exam_qs.aggregate(exam_count=Count('id'), avg_score=Avg('earned_score'))

        study_qs = DailyStudyLog.objects.filter(user=user)
        if since:
            study_qs = study_qs.filter(study_date__gte=since.date())
        study_agg = study_qs.aggregate(
            practice_count=Sum('practice_count'),
            correct_count=Sum('correct_count'),
            study_days=Count('id'),
        )

        last_log = DailyStudyLog.objects.filter(user=user).order_by('-study_date').first()

        students.append({
            'user_id':        user.id,
            'nickname':       p.nickname if p else user.username,
            'phone':          p.phone if p else '',
            'current_level':  p.current_level if p else 1,
            'exam_count':     exam_agg['exam_count'] or 0,
            'avg_score':      round(exam_agg['avg_score'] or 0, 1),
            'practice_count': study_agg['practice_count'] or 0,
            'correct_count':  study_agg['correct_count'] or 0,
            'study_days':     study_agg['study_days'] or 0,
            'last_active':    last_log.study_date.isoformat() if last_log else None,
            'joined_at':      m.joined_at.isoformat(),
        })

    return Response({
        'classroom': {
            'id':          classroom.id,
            'name':        classroom.name,
            'description': classroom.description,
            'level_name':  classroom.level.name if classroom.level else '',
        },
        'students': students,
    })


@api_view(['GET'])
@permission_classes([IsTeacherOrAdmin])
def teacher_student_exams(request, pk, user_id):
    """某学员的模考记录（下钻）"""
    try:
        classroom = _get_teacher_classroom(request, pk)
    except Classroom.DoesNotExist:
        return Response({'detail': '班级不存在或无权访问'}, status=404)

    if not ClassroomMember.objects.filter(classroom=classroom, user_id=user_id).exists():
        return Response({'detail': '该学员不在此班级'}, status=404)

    days_str = request.query_params.get('days', '30')
    since = _since(days_str)

    qs = ExamRecord.objects.filter(user_id=user_id).exclude(status=0)\
        .select_related('level', 'template').order_by('-created_at')
    if since:
        qs = qs.filter(created_at__gte=since)

    result = []
    for r in qs:
        passed = r.earned_score >= (
            r.template.pass_score if r.template else (r.total_score * 60 // 100)
        )
        result.append({
            'id':           r.id,
            'exam_name':    r.template.name if r.template else '随机组卷',
            'level_name':   r.level.name if r.level else '',
            'exam_type':    r.exam_type,
            'earned_score': r.earned_score,
            'total_score':  r.total_score,
            'passed':       passed,
            'status':       r.status,
            'created_at':   r.created_at.isoformat(),
        })
    return Response(result)
