from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import (
    RegisterSerializer, LoginSerializer, SmsLoginSerializer,
    SmsSendSerializer, ResetPasswordSerializer,
    UserProfileSerializer, ChangePasswordSerializer,
)
from .utils import send_sms_code, verify_sms_code


@api_view(['POST'])
@permission_classes([AllowAny])
def sms_send(request):
    serializer = SmsSendSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data['phone']
    purpose = serializer.validated_data['purpose']

    if purpose == 'register' and UserProfile.objects.filter(phone=phone).exists():
        return Response({'detail': '该手机号已注册'}, status=400)
    if purpose in ('login', 'reset_password') and not UserProfile.objects.filter(phone=phone).exists():
        return Response({'detail': '该手机号未注册'}, status=400)

    ok, msg = send_sms_code(phone, purpose)
    if not ok:
        return Response({'detail': msg}, status=429)
    return Response({'detail': msg})


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if not verify_sms_code(data['phone'], data['code'], 'register'):
        return Response({'detail': '验证码错误或已过期'}, status=400)

    user = User.objects.create_user(
        username=data['phone'],
        password=data['password'],
    )
    UserProfile.objects.create(
        user=user,
        phone=data['phone'],
        nickname=data.get('nickname', ''),
    )

    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data['phone']
    password = serializer.validated_data['password']

    try:
        profile = UserProfile.objects.get(phone=phone)
        user = profile.user
    except UserProfile.DoesNotExist:
        return Response({'detail': '手机号未注册'}, status=400)

    if not user.check_password(password):
        return Response({'detail': '密码错误'}, status=400)

    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def sms_login(request):
    serializer = SmsLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    phone = serializer.validated_data['phone']
    code = serializer.validated_data['code']

    if not verify_sms_code(phone, code, 'login'):
        return Response({'detail': '验证码错误或已过期'}, status=400)

    try:
        profile = UserProfile.objects.get(phone=phone)
        user = profile.user
    except UserProfile.DoesNotExist:
        return Response({'detail': '手机号未注册'}, status=400)

    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    serializer = ResetPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if not verify_sms_code(data['phone'], data['code'], 'reset_password'):
        return Response({'detail': '验证码错误或已过期'}, status=400)

    try:
        profile = UserProfile.objects.get(phone=data['phone'])
        user = profile.user
    except UserProfile.DoesNotExist:
        return Response({'detail': '手机号未注册'}, status=400)

    user.set_password(data['new_password'])
    user.save()
    return Response({'detail': '密码重置成功'})


class ProfileView(APIView):
    def get(self, request):
        profile = request.user.profile
        return Response(UserProfileSerializer(profile).data)

    def put(self, request):
        profile = request.user.profile
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AvatarUploadView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get('avatar')
        if not file:
            return Response({'detail': '请上传头像文件'}, status=400)
        profile = request.user.profile
        profile.avatar = file
        profile.save(update_fields=['avatar'])
        return Response({'avatar': profile.avatar.url})


class ChangePasswordView(APIView):
    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({'detail': '原密码错误'}, status=400)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': '密码修改成功'})
