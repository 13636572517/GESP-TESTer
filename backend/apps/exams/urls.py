from django.urls import path
from . import views

urlpatterns = [
    path('exams/templates/', views.ExamTemplateListView.as_view(), name='exam-template-list'),
    path('exams/start/', views.start_exam, name='exam-start'),
    path('exams/<int:record_id>/', views.get_exam, name='exam-detail'),
    path('exams/<int:record_id>/answer/', views.save_answer, name='exam-save-answer'),
    path('exams/<int:record_id>/submit/', views.submit_exam, name='exam-submit'),
    path('exams/<int:record_id>/switch/', views.report_switch, name='exam-switch'),
    path('exams/<int:record_id>/result/', views.exam_result, name='exam-result'),
    path('exams/history/', views.ExamHistoryView.as_view(), name='exam-history'),
    # 管理端
    path('admin/exam-templates/export/', views.export_exam_templates, name='admin-template-export'),
    path('admin/exam-templates/import/', views.import_exam_templates, name='admin-template-import'),
    path('admin/exam-templates/', views.AdminExamTemplateListCreateView.as_view(), name='admin-template-list'),
    path('admin/exam-templates/<int:pk>/', views.AdminExamTemplateDetailView.as_view(), name='admin-template-detail'),
]
