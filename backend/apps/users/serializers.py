from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Classroom, ClassroomMember


class RegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=11, min_length=11)
    password = serializers.CharField(min_length=6, max_length=32, write_only=True)
    code = serializers.CharField(max_length=6)
    nickname = serializers.CharField(max_length=50, required=False, default='')

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('手机号格式不正确')
        if UserProfile.objects.filter(phone=value).exists():
            raise serializers.ValidationError('该手机号已注册')
        return value


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=11)
    password = serializers.CharField(write_only=True)


class SmsLoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)


class SmsSendSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=11, min_length=11)
    purpose = serializers.ChoiceField(choices=['register', 'login', 'reset_password'])

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('手机号格式不正确')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=6, max_length=32)


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'phone', 'avatar', 'nickname', 'current_level', 'is_admin', 'created_at']
        read_only_fields = ['id', 'phone', 'is_admin', 'created_at']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=6, max_length=32, write_only=True)


# ── Admin serializers ──────────────────────────────────────────

class AdminUserSerializer(serializers.ModelSerializer):
    """用于管理员列表展示和编辑的用户序列化器"""
    nickname = serializers.CharField(source='profile.nickname', read_only=True)
    phone = serializers.CharField(source='profile.phone', read_only=True)
    current_level = serializers.IntegerField(source='profile.current_level', read_only=True)
    is_admin = serializers.BooleanField(source='profile.is_admin', read_only=True)
    avatar = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='profile.created_at', read_only=True)
    class_names = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'phone', 'nickname', 'current_level', 'is_admin', 'avatar', 'created_at', 'class_names']

    def get_avatar(self, obj):
        try:
            if obj.profile.avatar:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.profile.avatar.url)
        except Exception:
            pass
        return ''

    def get_class_names(self, obj):
        return list(obj.classrooms.values_list('classroom__name', flat=True))


class ClassroomMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    phone = serializers.CharField(source='user.profile.phone', read_only=True)
    nickname = serializers.CharField(source='user.profile.nickname', read_only=True)
    current_level = serializers.IntegerField(source='user.profile.current_level', read_only=True)
    note = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = ClassroomMember
        fields = ['id', 'user_id', 'phone', 'nickname', 'current_level', 'note', 'joined_at']


class ClassroomSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source='level.name', read_only=True, default='')
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Classroom
        fields = ['id', 'name', 'description', 'level', 'level_name', 'is_active', 'member_count', 'created_at']
        read_only_fields = ['id', 'created_at']
