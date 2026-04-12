from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('avatar/', views.AvatarUploadView.as_view(), name='avatar-upload'),
    path('password/', views.ChangePasswordView.as_view(), name='change-password'),
]
