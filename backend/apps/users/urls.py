from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('sms/send/', views.sms_send, name='sms-send'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('login/sms/', views.sms_login, name='sms-login'),
    path('login/username/', views.login_by_username, name='login-username'),
    path('password/reset/', views.reset_password, name='reset-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
