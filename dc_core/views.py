from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated

class RootAPIView(APIView):
    """API根视图"""
    authentication_classes = [TokenAuthentication]
    permission_classes = []
    
    def get(self, request):
        """获取API根信息"""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        return Response({
            "message": "欢迎使用数据采集API",
            "version": "1.0",
            "endpoints": {
                "restricted": "/api/v1/restricted/"
            }
        })

class RestrictedViewSet(viewsets.ViewSet):
    """受限资源访问的ViewSet"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        return Response({"message": "这是一个受限资源"})
        
    def create(self, request):
        return Response({"message": "创建受限资源"}) 