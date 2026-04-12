from django.urls import path
from . import views

urlpatterns = [
    path('practice/start/', views.start_practice, name='practice-start'),
    path('practice/<int:session_id>/submit/', views.submit_answer, name='practice-submit'),
    path('practice/<int:session_id>/finish/', views.finish_practice, name='practice-finish'),
    path('practice/history/', views.PracticeHistoryView.as_view(), name='practice-history'),
    # 错题本
    path('mistakes/', views.MistakeListView.as_view(), name='mistake-list'),
    path('mistakes/stats/', views.mistake_stats, name='mistake-stats'),
    path('mistakes/review/', views.mistake_review, name='mistake-review'),
    path('mistakes/<int:pk>/mastered/', views.mark_mastered, name='mistake-mastered'),
]
