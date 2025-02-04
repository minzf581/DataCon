from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response

class ProjectViewSet(viewsets.ModelViewSet):
    """
    项目视图集
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return []  # 暂时返回空列表
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def root(self, request):
        return Response({})

class DatasetViewSet(viewsets.ModelViewSet):
    """
    数据集视图集
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return []  # 暂时返回空列表

class TaskViewSet(viewsets.ModelViewSet):
    """
    任务视图集
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return []  # 暂时返回空列表

class TaskInputViewSet(viewsets.ModelViewSet):
    """
    任务输入视图集
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return []  # 暂时返回空列表 