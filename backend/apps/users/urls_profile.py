from django.urls import path
from . import views
from . import views_ai

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('avatar/', views.AvatarUploadView.as_view(), name='avatar-upload'),
    path('password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('ai-config/', views_ai.user_ai_config, name='user-ai-config'),
    path('ai-config/test/', views_ai.user_ai_test, name='user-ai-test'),
    path('ai-usage/', views_ai.user_ai_usage, name='user-ai-usage'),
    path('ai-explain/', views_ai.ai_explain_stream, name='user-ai-explain'),
]
