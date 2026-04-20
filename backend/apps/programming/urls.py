from django.urls import path
from . import views

urlpatterns = [
    path('programming/questions/', views.question_list),
    path('programming/questions/<int:pk>/', views.question_detail),
    path('programming/questions/<int:pk>/submit/', views.submit_code),
    path('programming/questions/<int:pk>/submissions/', views.my_submissions),
    # 管理员
    path('admin/programming/questions/', views.admin_question_list),
    path('admin/programming/questions/<int:pk>/', views.admin_question_detail),
    path('admin/programming/questions/<int:pk>/test-cases/', views.admin_test_cases),
]
