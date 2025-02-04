from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from dc_core.api import ProjectViewSet, DatasetViewSet, TaskViewSet
from .views import RootAPIView, RestrictedAPIView

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'datasets', DatasetViewSet, basename='dataset')
router.register(r'tasks', TaskViewSet, basename='task')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', RootAPIView.as_view(), name='api-root'),
    path('api/v1/restricted/', RestrictedAPIView.as_view(), name='api-restricted'),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
] 