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
]
