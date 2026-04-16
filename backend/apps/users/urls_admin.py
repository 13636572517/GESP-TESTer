from django.urls import path
from . import views_admin

urlpatterns = [
    # 会员管理
    path('users/', views_admin.user_list, name='admin-user-list'),
    path('users/<int:pk>/', views_admin.user_detail, name='admin-user-detail'),
    # 班级管理
    path('classes/', views_admin.classroom_list, name='admin-classroom-list'),
    path('classes/<int:pk>/', views_admin.classroom_detail, name='admin-classroom-detail'),
    path('classes/<int:pk>/members/', views_admin.classroom_members, name='admin-classroom-members'),
    path('classes/<int:pk>/members/<int:member_id>/', views_admin.classroom_member_detail, name='admin-classroom-member-detail'),
]
