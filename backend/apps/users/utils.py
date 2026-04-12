import random
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import SmsCode

logger = logging.getLogger(__name__)


def generate_code():
    return f'{random.randint(0, 999999):06d}'


def send_sms_code(phone, purpose):
    """发送短信验证码"""
    # 检查发送频率：同一手机号同一用途1分钟内只能发一次
    one_min_ago = timezone.now() - timedelta(minutes=1)
    recent = SmsCode.objects.filter(
        phone=phone, purpose=purpose, created_at__gte=one_min_ago
    ).exists()
    if recent:
        return False, '发送太频繁，请1分钟后再试'

    code = generate_code()
    expired_at = timezone.now() + timedelta(minutes=settings.SMS_CODE_EXPIRY)

    SmsCode.objects.create(
        phone=phone,
        code=code,
        purpose=purpose,
        expired_at=expired_at,
    )

    backend = getattr(settings, 'SMS_BACKEND', 'console')
    if backend == 'console':
        logger.info(f'[SMS] 手机号: {phone}, 验证码: {code}, 用途: {purpose}')
        print(f'[SMS] 手机号: {phone}, 验证码: {code}, 用途: {purpose}')
    else:
        # TODO: 接入阿里云SMS
        pass

    return True, '验证码已发送'


def verify_sms_code(phone, code, purpose):
    """验证短信验证码"""
    record = SmsCode.objects.filter(
        phone=phone,
        code=code,
        purpose=purpose,
        is_used=False,
        expired_at__gte=timezone.now(),
    ).order_by('-created_at').first()

    if not record:
        return False
    record.is_used = True
    record.save(update_fields=['is_used'])
    return True
