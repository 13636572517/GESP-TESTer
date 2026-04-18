from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import UserProfile, Classroom, ClassroomMember
from .serializers import AdminUserSerializer, ClassroomSerializer, ClassroomMemberSerializer


class AdminPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return hasattr(request.user, 'profile') and request.user.profile.is_admin


# ── 会员管理 ──────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([AdminPermission])
def user_list(request):
    """获取所有用户列表 / 管理员创建账号"""
    if request.method == 'POST':
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '').strip()
        nickname = request.data.get('nickname', '').strip()
        current_level = int(request.data.get('current_level', 1))
        is_admin_flag = bool(request.data.get('is_admin', False))

        if not username:
            return Response({'detail': '用户名不能为空'}, status=400)
        if len(password) < 6:
            return Response({'detail': '密码至少6位'}, status=400)
        if User.objects.filter(username=username).exists():
            return Response({'detail': f'用户名「{username}」已存在'}, status=400)

        user = User.objects.create_user(username=username, password=password)
        UserProfile.objects.create(
            user=user,
            phone=None,
            nickname=nickname or username,
            current_level=current_level,
            is_admin=is_admin_flag,
        )
        serializer = AdminUserSerializer(user, context={'request': request})
        return Response(serializer.data, status=201)

    qs = User.objects.select_related('profile').prefetch_related('classrooms__classroom').order_by('-profile__created_at')

    search = request.query_params.get('search', '').strip()
    if search:
        qs = qs.filter(
            Q(profile__phone__icontains=search) | Q(profile__nickname__icontains=search)
        )

    level = request.query_params.get('level')
    if level:
        qs = qs.filter(profile__current_level=level)

    is_admin = request.query_params.get('is_admin')
    if is_admin is not None:
        qs = qs.filter(profile__is_admin=(is_admin == 'true'))

    # Simple pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    total = qs.count()
    qs = qs[(page - 1) * page_size: page * page_size]

    serializer = AdminUserSerializer(qs, many=True, context={'request': request})
    return Response({'count': total, 'results': serializer.data})


@api_view(['PUT', 'DELETE'])
@permission_classes([AdminPermission])
def user_detail(request, pk):
    """更新或删除用户"""
    try:
        user = User.objects.select_related('profile').get(pk=pk)
    except User.DoesNotExist:
        return Response({'detail': '用户不存在'}, status=404)

    if request.method == 'DELETE':
        if user == request.user:
            return Response({'detail': '不能删除自己'}, status=400)
        user.delete()
        return Response(status=204)

    # PUT: update profile fields + optional password reset
    profile = user.profile
    data = request.data
    if 'nickname' in data:
        profile.nickname = data['nickname']
    if 'current_level' in data:
        level = int(data['current_level'])
        if 1 <= level <= 8:
            profile.current_level = level
    if 'is_admin' in data:
        if user == request.user and not data['is_admin']:
            return Response({'detail': '不能取消自己的管理员权限'}, status=400)
        profile.is_admin = bool(data['is_admin'])
    profile.save()
    # 可选：重置密码
    new_password = data.get('new_password', '').strip()
    if new_password:
        if len(new_password) < 6:
            return Response({'detail': '密码至少6位'}, status=400)
        user.set_password(new_password)
        user.save()

    serializer = AdminUserSerializer(user, context={'request': request})
    return Response(serializer.data)


# ── 班级管理 ──────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([AdminPermission])
def classroom_list(request):
    """获取班级列表 / 创建班级"""
    if request.method == 'POST':
        serializer = ClassroomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        classroom = serializer.save()
        return Response(ClassroomSerializer(classroom).data, status=201)

    qs = Classroom.objects.select_related('level').all()
    search = request.query_params.get('search', '').strip()
    if search:
        qs = qs.filter(name__icontains=search)

    classrooms = []
    for c in qs:
        data = ClassroomSerializer(c).data
        data['member_count'] = c.members.count()
        classrooms.append(data)
    return Response(classrooms)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([AdminPermission])
def classroom_detail(request, pk):
    """获取 / 更新 / 删除班级"""
    try:
        classroom = Classroom.objects.select_related('level').get(pk=pk)
    except Classroom.DoesNotExist:
        return Response({'detail': '班级不存在'}, status=404)

    if request.method == 'DELETE':
        classroom.delete()
        return Response(status=204)

    if request.method == 'PUT':
        serializer = ClassroomSerializer(classroom, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        data = ClassroomSerializer(classroom).data
        data['member_count'] = classroom.members.count()
        return Response(data)

    # GET
    data = ClassroomSerializer(classroom).data
    data['member_count'] = classroom.members.count()
    return Response(data)


@api_view(['GET', 'POST'])
@permission_classes([AdminPermission])
def classroom_members(request, pk):
    """获取班级成员列表 / 添加成员"""
    try:
        classroom = Classroom.objects.get(pk=pk)
    except Classroom.DoesNotExist:
        return Response({'detail': '班级不存在'}, status=404)

    if request.method == 'POST':
        phone = request.data.get('phone', '').strip()
        note = request.data.get('note', '').strip()
        try:
            profile = UserProfile.objects.select_related('user').get(phone=phone)
        except UserProfile.DoesNotExist:
            return Response({'detail': f'手机号 {phone} 未注册'}, status=400)

        member, created = ClassroomMember.objects.get_or_create(
            classroom=classroom,
            user=profile.user,
            defaults={'note': note},
        )
        if not created:
            return Response({'detail': '该学员已在班级中'}, status=400)
        return Response(ClassroomMemberSerializer(member).data, status=201)

    members = ClassroomMember.objects.filter(classroom=classroom).select_related(
        'user__profile'
    )
    return Response(ClassroomMemberSerializer(members, many=True).data)


@api_view(['PUT', 'DELETE'])
@permission_classes([AdminPermission])
def classroom_member_detail(request, pk, member_id):
    """更新备注 / 移出班级"""
    try:
        member = ClassroomMember.objects.select_related('user__profile').get(pk=member_id, classroom_id=pk)
    except ClassroomMember.DoesNotExist:
        return Response({'detail': '成员不存在'}, status=404)

    if request.method == 'DELETE':
        member.delete()
        return Response(status=204)

    # PUT: update note
    member.note = request.data.get('note', member.note)
    member.save()
    return Response(ClassroomMemberSerializer(member).data)
