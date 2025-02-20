from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

class FinancialDataViewSet(viewsets.ViewSet):
    """金融数据 API 视图集"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def market_data(self, request):
        """获取市场数据
        
        参数:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: 数据间隔 (1d, 1h, 15m 等)
        """
        try:
            symbol = request.query_params.get('symbol', 'AAPL')
            start_date = request.query_params.get('start_date', 
                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
            end_date = request.query_params.get('end_date', 
                datetime.now().strftime('%Y-%m-%d'))
            interval = request.query_params.get('interval', '1d')

            # 获取市场数据
            ticker = yf.Ticker(symbol)
            hist = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval
            )

            # 转换为 JSON 格式
            data = {
                'symbol': symbol,
                'data': hist.reset_index().to_dict('records'),
                'info': ticker.info
            }

            return Response(data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def technical_indicators(self, request):
        """获取技术指标
        
        参数:
            symbol: 股票代码
            indicator: 指标类型 (MA, RSI, MACD 等)
            period: 周期
        """
        try:
            symbol = request.query_params.get('symbol', 'AAPL')
            indicator = request.query_params.get('indicator', 'MA')
            period = int(request.query_params.get('period', 14))

            # 获取历史数据
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='1y')

            # 计算技术指标
            if indicator == 'MA':
                hist['MA'] = hist['Close'].rolling(window=period).mean()
            elif indicator == 'RSI':
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                hist['RSI'] = 100 - (100 / (1 + rs))
            elif indicator == 'MACD':
                exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
                exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
                hist['MACD'] = exp1 - exp2
                hist['Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()

            # 转换为 JSON 格式
            data = {
                'symbol': symbol,
                'indicator': indicator,
                'period': period,
                'data': hist.reset_index().to_dict('records')
            }

            return Response(data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def fundamental_data(self, request):
        """获取基本面数据
        
        参数:
            symbol: 股票代码
            data_type: 数据类型 (financials, balance_sheet, cashflow 等)
        """
        try:
            symbol = request.query_params.get('symbol', 'AAPL')
            data_type = request.query_params.get('data_type', 'financials')

            # 获取基本面数据
            ticker = yf.Ticker(symbol)
            
            if data_type == 'financials':
                data = ticker.financials.to_dict()
            elif data_type == 'balance_sheet':
                data = ticker.balance_sheet.to_dict()
            elif data_type == 'cashflow':
                data = ticker.cashflow.to_dict()
            else:
                data = ticker.info

            return Response({
                'symbol': symbol,
                'data_type': data_type,
                'data': data
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def market_sentiment(self, request):
        """获取市场情绪数据
        
        参数:
            symbol: 股票代码
            period: 分析周期 (天数)
        """
        try:
            symbol = request.query_params.get('symbol', 'AAPL')
            period = int(request.query_params.get('period', 30))

            # 获取历史数据
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f'{period}d')

            # 计算基本情绪指标
            hist['Daily_Return'] = hist['Close'].pct_change()
            hist['Volatility'] = hist['Daily_Return'].rolling(window=20).std()
            hist['Volume_MA'] = hist['Volume'].rolling(window=20).mean()
            
            # 计算情绪指标
            sentiment_data = {
                'price_momentum': float(hist['Daily_Return'].mean()),
                'volatility': float(hist['Volatility'].mean()),
                'volume_trend': float(hist['Volume'].mean() / hist['Volume_MA'].mean()),
                'price_trend': 'Bullish' if hist['Close'].iloc[-1] > hist['Close'].mean() else 'Bearish'
            }

            return Response({
                'symbol': symbol,
                'period': period,
                'sentiment': sentiment_data,
                'history': hist.reset_index().tail(5).to_dict('records')
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            ) 