from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from dc_core.api import ProjectViewSet, DatasetViewSet, TaskViewSet
from dc_core.api.financial_data import FinancialDataViewSet

# 创建路由器实例
router = DefaultRouter()

# 注册视图集
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'datasets', DatasetViewSet, basename='dataset')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'financial', FinancialDataViewSet, basename='financial')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
] 