from django.urls import path
from . import views

urlpatterns = [
    path('admin/questions/', views.QuestionListCreateView.as_view(), name='question-list-create'),
    path('admin/questions/<int:pk>/', views.QuestionDetailView.as_view(), name='question-detail'),
    path('admin/questions/batch/', views.batch_create_questions, name='question-batch'),
    path('admin/questions/import-csv/', views.import_csv, name='question-import-csv'),
    path('admin/questions/export/', views.export_questions, name='question-export'),
    path('admin/questions/csv-template/', views.download_csv_template, name='question-csv-template'),
    path('admin/questions/batch-delete/', views.batch_delete_questions, name='question-batch-delete'),
    path('admin/questions/pdf-extract/', views.pdf_extract, name='question-pdf-extract'),
    path('admin/questions/pdf-import/', views.pdf_import_confirm, name='question-pdf-import'),
    # AI 功能
    path('admin/questions/ai-suggest-tags/', views.ai_suggest_tags, name='question-ai-suggest-tags'),
    path('admin/questions/ai-confirm-tags/', views.ai_confirm_tags, name='question-ai-confirm-tags'),
    path('admin/questions/ai-generate/', views.ai_generate_questions, name='question-ai-generate'),
    # AI 配置与统计
    path('admin/ai-config/', views.ai_config_view, name='ai-config'),
    path('admin/ai-config/test/', views.ai_test_model, name='ai-test-model'),
    path('admin/ai-usage/', views.ai_usage_stats, name='ai-usage-stats'),
]
