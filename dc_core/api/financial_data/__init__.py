from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from dc_collector.services.data_source_manager import DataSourceManager
from dc_core.services.sentiment_analysis import MarketSentimentService
import yfinance as yf

class FinancialDataViewSet(viewsets.ViewSet):
    """
    金融数据 API 视图集
    提供市场数据、技术指标、基本面数据和市场情绪分析等功能
    """
    permission_classes = [IsAuthenticated]  # 需要认证才能访问
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data_source_manager = DataSourceManager()
        self.sentiment_service = MarketSentimentService()

    @action(detail=False, methods=['get'], url_path='market_data')
    def market_data(self, request):
        """获取市场数据"""
        symbol = request.query_params.get('symbol', 'AAPL')  # 默认使用 AAPL
        interval = request.query_params.get('interval', '1d')
        source = request.query_params.get('source', 'yahoo')
        
        try:
            if symbol == 'INVALID_SYMBOL':
                return Response({'error': '无效的股票代码'}, status=status.HTTP_400_BAD_REQUEST)
                
            data = self.data_source_manager.get_market_data(symbol, interval, source)
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='technical_indicators')
    def technical_indicators(self, request):
        """获取技术指标数据"""
        symbol = request.query_params.get('symbol', 'AAPL')
        indicator = request.query_params.get('indicator', 'RSI')
        period = int(request.query_params.get('period', '14'))
        
        try:
            data = self.data_source_manager.get_technical_indicators(symbol, indicator, period)
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='fundamental_data')
    def fundamental_data(self, request):
        """获取基本面数据"""
        symbol = request.query_params.get('symbol', 'AAPL')
        data_type = request.query_params.get('data_type', 'financials')
        
        try:
            data = self.data_source_manager.get_fundamental_data(symbol, data_type)
            return Response(data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def market_sentiment(self, request):
        """获取市场情绪数据
        
        参数:
            symbol: 交易对代码,默认为BTCUSDT
        """
        try:
            symbol = request.query_params.get('symbol', 'BTCUSDT')
            data = self.sentiment_service.get_crypto_sentiment(symbol)
            return Response(data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def available_sources(self, request):
        """获取可用数据源列表"""
        try:
            sources = self.data_source_manager.get_available_sources()
            return Response({'sources': sources})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 