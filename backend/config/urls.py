from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/user/', include('apps.users.urls_profile')),
    path('api/', include('apps.knowledge.urls')),
    path('api/', include('apps.questions.urls')),
    path('api/', include('apps.practice.urls')),
    path('api/', include('apps.exams.urls')),
    path('api/', include('apps.stats.urls')),
    path('api/admin/', include('apps.users.urls_admin')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
