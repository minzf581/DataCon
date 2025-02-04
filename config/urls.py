from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from dc_core.api import ProjectViewSet, DatasetViewSet, TaskViewSet, TaskInputViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'datasets', DatasetViewSet, basename='dataset')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'task-inputs', TaskInputViewSet, basename='task-input')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', ProjectViewSet.as_view({'get': 'root'})),
    path('api/v1/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
] 