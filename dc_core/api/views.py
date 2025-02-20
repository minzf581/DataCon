from rest_framework import viewsets, status
from rest_framework.response import Response
from dc_core.models import Project, Dataset, Task
from rest_framework.decorators import api_view
from ..services.market_data import MarketDataService, DataSourceError
import logging

logger = logging.getLogger(__name__)

class ProjectViewSet(viewsets.ModelViewSet):
    """项目视图集"""
    queryset = Project.objects.all()
    
    def list(self, request):
        """列出所有项目"""
        projects = self.queryset.values('id', 'name', 'description', 'created_at')
        return Response(list(projects))
        
    def create(self, request):
        """创建新项目"""
        name = request.data.get('name')
        description = request.data.get('description')
        
        if not name:
            return Response({'error': '项目名称不能为空'}, status=status.HTTP_400_BAD_REQUEST)
            
        project = Project.objects.create(name=name, description=description)
        return Response({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'created_at': project.created_at
        }, status=status.HTTP_201_CREATED)

class DatasetViewSet(viewsets.ModelViewSet):
    """数据集视图集"""
    queryset = Dataset.objects.all()
    
    def list(self, request):
        """列出所有数据集"""
        datasets = self.queryset.values('id', 'name', 'description', 'created_at')
        return Response(list(datasets))
        
    def create(self, request):
        """创建新数据集"""
        name = request.data.get('name')
        description = request.data.get('description')
        
        if not name:
            return Response({'error': '数据集名称不能为空'}, status=status.HTTP_400_BAD_REQUEST)
            
        dataset = Dataset.objects.create(name=name, description=description)
        return Response({
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'created_at': dataset.created_at
        }, status=status.HTTP_201_CREATED)

class TaskViewSet(viewsets.ModelViewSet):
    """任务视图集"""
    queryset = Task.objects.all()
    
    def list(self, request):
        """列出所有任务"""
        tasks = self.queryset.values('id', 'name', 'status', 'created_at')
        return Response(list(tasks))
        
    def create(self, request):
        """创建新任务"""
        name = request.data.get('name')
        description = request.data.get('description')
        
        if not name:
            return Response({'error': '任务名称不能为空'}, status=status.HTTP_400_BAD_REQUEST)
            
        task = Task.objects.create(name=name, description=description)
        return Response({
            'id': task.id,
            'name': task.name,
            'description': task.description,
            'status': task.status,
            'created_at': task.created_at
        }, status=status.HTTP_201_CREATED)

@api_view(['GET'])
async def get_stock_data(request):
    """获取股票数据
    
    GET /api/v1/market-data/?symbol=AAPL
    
    参数:
        symbol (str): 股票代码，例如 'AAPL', 'GOOGL'
        
    返回:
        {
            'price': float,    # 当前价格
            'volume': int,     # 成交量
            'timestamp': str,  # 时间戳
            'source': str      # 数据来源
        }
    """
    symbol = request.query_params.get('symbol')
    
    if not symbol:
        return Response(
            {"error": "股票代码不能为空", "code": "MISSING_SYMBOL"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        service = MarketDataService()
        data = await service.get_stock_data(symbol)
        return Response(data)
        
    except DataSourceError as e:
        logger.error(f"数据源错误: {e}")
        return Response(
            {"error": str(e), "code": "DATA_SOURCE_ERROR"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
    except Exception as e:
        logger.error(f"未知错误: {e}")
        return Response(
            {"error": "服务器内部错误", "code": "INTERNAL_ERROR"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 