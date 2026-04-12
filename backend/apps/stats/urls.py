from django.urls import path
from . import views

urlpatterns = [
    path('stats/overview/', views.overview, name='stats-overview'),
    path('stats/mastery/', views.mastery, name='stats-mastery'),
    path('stats/daily/', views.daily_stats, name='stats-daily'),
    path('stats/weakness/', views.weakness, name='stats-weakness'),
]
