from django.urls import path
from . import views

urlpatterns = [
    path('levels/', views.LevelListView.as_view(), name='level-list'),
    path('levels/<int:level_id>/chapters/', views.ChapterListView.as_view(), name='chapter-list'),
    path('chapters/<int:chapter_id>/points/', views.KnowledgePointListView.as_view(), name='point-list'),
    path('knowledge/<int:pk>/', views.KnowledgePointDetailView.as_view(), name='knowledge-detail'),
    path('knowledge/tree/', views.knowledge_tree, name='knowledge-tree'),
    path('admin/knowledge/<int:pk>/content/', views.update_knowledge_content, name='knowledge-content-update'),
]
