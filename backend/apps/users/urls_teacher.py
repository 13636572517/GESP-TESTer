from django.urls import path
from . import views_teacher

urlpatterns = [
    path('classes/', views_teacher.teacher_classes, name='teacher-classes'),
    path('classes/<int:pk>/overview/', views_teacher.teacher_class_overview, name='teacher-class-overview'),
    path('classes/<int:pk>/students/<int:user_id>/exams/', views_teacher.teacher_student_exams, name='teacher-student-exams'),
]
