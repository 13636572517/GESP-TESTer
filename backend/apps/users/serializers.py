from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


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
