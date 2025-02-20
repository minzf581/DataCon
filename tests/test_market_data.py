"""
市场数据服务测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from dc_core.services.market_data import MarketDataService, DataSourceError
from dc_core.services.sentiment_analysis import MarketSentimentService
import pandas as pd
from datetime import datetime
from binance.exceptions import BinanceAPIException

@pytest.fixture
def service():
    """创建市场数据服务实例"""
    return MarketDataService()

def test_get_stock_data_success(service):
    """测试成功获取股票数据"""
    mock_hist = pd.DataFrame({
        'Open': [150.0],
        'High': [155.0],
        'Low': [148.0],
        'Close': [152.0],
        'Volume': [1000000]
    }, index=[pd.Timestamp('2024-02-10')])
    
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = mock_hist
    
    with patch.object(service, 'yf_client', return_value=mock_ticker):
        data = service.get_stock_data('AAPL')
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'market_data' in data['data']
        assert 'current_price' in data['data']
        assert 'volume' in data['data']
        assert 'timestamp' in data['data']
        assert 'source' in data['data']
        assert data['data']['source'] == 'yahoo'
        assert data['data']['current_price'] == 152.0
        assert data['data']['volume'] == 1000000

def test_get_stock_data_invalid_symbol(service):
    """测试获取无效股票代码数据"""
    mock_ticker = MagicMock()
    mock_ticker.history.side_effect = Exception("Invalid symbol")
    
    with patch.object(service, 'yf_client', return_value=mock_ticker):
        with pytest.raises(DataSourceError):
            service.get_stock_data('INVALID_SYMBOL')

def test_get_stock_data_empty_symbol(service):
    """测试获取空股票代码数据"""
    with pytest.raises(ValueError):
        service.get_stock_data('')

def test_get_crypto_data_success(service):
    """测试成功获取加密货币数据"""
    mock_klines = [[
        1234567890000,  # timestamp
        "50000.00",     # open
        "51000.00",     # high
        "49000.00",     # low
        "50500.00",     # close
        "100.00",       # volume
    ]]
    
    mock_ticker = {
        'lastPrice': "50500.00",
        'priceChange': "500.00",
        'priceChangePercent': "1.00"
    }
    
    mock_depth = {
        'bids': [["50000.00", "1.00"], ["49900.00", "2.00"]],
        'asks': [["50100.00", "1.00"], ["50200.00", "2.00"]]
    }
    
    with patch.object(service.binance, 'get_klines', return_value=mock_klines), \
         patch.object(service.binance, 'get_ticker', return_value=mock_ticker), \
         patch.object(service.binance, 'get_order_book', return_value=mock_depth):
        
        data = service.get_crypto_data('BTCUSDT')
        
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'market_data' in data['data']
        assert 'current_price' in data['data']
        assert 'price_change' in data['data']
        assert 'price_change_percent' in data['data']
        assert 'market_depth' in data['data']
        assert len(data['data']['market_depth']['bids']) == 2
        assert len(data['data']['market_depth']['asks']) == 2
        assert data['data']['source'] == 'binance'

def test_get_crypto_data_invalid_symbol(service):
    """测试获取无效交易对数据"""
    mock_response = Mock()
    mock_response.text = '{"code": -1121, "msg": "Invalid symbol"}'
    mock_response.status_code = 400
    
    with patch.object(service.binance, 'get_klines', side_effect=BinanceAPIException(
        response=mock_response,
        status_code=400,
        text='{"code": -1121, "msg": "Invalid symbol"}'
    )):
        with pytest.raises(DataSourceError) as exc_info:
            service.get_crypto_data('INVALID_PAIR')
        assert "Binance API错误" in str(exc_info.value)

def test_binance_market_depth(service):
    """测试获取市场深度数据"""
    mock_depth = {
        'bids': [["50000.00", "1.00"], ["49900.00", "2.00"]],
        'asks': [["50100.00", "1.00"], ["50200.00", "2.00"]]
    }
    
    with patch.object(service.binance, 'get_klines', return_value=[[1234567890000, "50000.00", "51000.00", "49000.00", "50500.00", "100.00"]]), \
         patch.object(service.binance, 'get_ticker', return_value={'lastPrice': "50500.00", 'priceChange': "500.00", 'priceChangePercent': "1.00"}), \
         patch.object(service.binance, 'get_order_book', return_value=mock_depth):
        
        data = service.get_crypto_data('BTCUSDT')
        assert len(data['data']['market_depth']['bids']) == 2
        assert len(data['data']['market_depth']['asks']) == 2
        assert float(data['data']['market_depth']['bids'][0][0]) < float(data['data']['market_depth']['asks'][0][0])

def test_binance_error_handling(service):
    """测试Binance错误处理"""
    mock_response = Mock()
    mock_response.text = '{"code": -1000, "msg": "Internal Server Error"}'
    mock_response.status_code = 500
    
    with patch.object(service.binance, 'get_klines', side_effect=BinanceAPIException(
        response=mock_response,
        status_code=500,
        text='{"code": -1000, "msg": "Internal Server Error"}'
    )):
        with pytest.raises(DataSourceError) as exc_info:
            service.get_crypto_data('BTCUSDT')
        assert "Binance API错误" in str(exc_info.value)

def test_get_crypto_sentiment_success(service):
    """测试成功获取加密货币市场情绪数据"""
    # 模拟K线数据
    mock_klines = [[
        1234567890000,  # timestamp
        "50000.00",     # open
        "51000.00",     # high
        "49000.00",     # low
        "50500.00",     # close
        "100.00",       # volume
        1234567890000,  # close_time
        "5000000.00",   # quote_volume
        100,            # trades
        "50.00",        # taker_base
        "2500000.00",   # taker_quote
        "0"             # ignore
    ]] * 24  # 24小时数据
    
    # 模拟市场深度数据
    mock_depth = {
        'bids': [["50000.00", "1.00"], ["49900.00", "2.00"]] * 10,
        'asks': [["50100.00", "1.00"], ["50200.00", "2.00"]] * 10
    }
    
    # 模拟24小时统计数据
    mock_ticker = {
        'volume': "1000.00",
        'quoteVolume': "50000000.00",
        'priceChangePercent': "2.5",
        'count': 10000,
        'weightedAvgPrice': "50000.00"
    }
    
    # 模拟大额交易数据
    mock_trades = [
        {'quoteQty': "100000.00", 'price': "50000.00", 'qty': "2.00"}
    ] * 100
    
    sentiment_service = MarketSentimentService()
    
    with patch.object(sentiment_service.binance, 'get_klines', return_value=mock_klines), \
         patch.object(sentiment_service.binance, 'get_order_book', return_value=mock_depth), \
         patch.object(sentiment_service.binance, 'get_ticker', return_value=mock_ticker), \
         patch.object(sentiment_service.binance, 'get_recent_trades', return_value=mock_trades):
        
        data = sentiment_service.get_crypto_sentiment('BTCUSDT')
        
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'sentiment_score' in data['data']
        assert 'sentiment_label' in data['data']
        assert 'technical_analysis' in data['data']
        assert 'market_depth' in data['data']
        assert 'volume_analysis' in data['data']
        assert 'whale_activity' in data['data']
        assert 'details' in data['data']
        
        # 验证技术指标
        tech = data['data']['technical_analysis']
        assert 'rsi' in tech
        assert 'macd' in tech
        assert 'bollinger_bands' in tech
        
        # 验证市场深度
        depth = data['data']['market_depth']
        assert 'buy_pressure' in depth
        assert 'sell_pressure' in depth
        assert 'pressure_ratio' in depth
        assert 'spread' in depth
        
        # 验证交易量分析
        volume = data['data']['volume_analysis']
        assert 'volume_24h' in volume
        assert 'quote_volume_24h' in volume
        assert 'price_change_percent' in volume
        assert 'trades_24h' in volume
        
        # 验证大户活动
        whale = data['data']['whale_activity']
        assert 'whale_trades_count' in whale
        assert 'total_whale_volume' in whale
        assert 'avg_whale_trade_size' in whale

def test_get_crypto_sentiment_error(service):
    """测试获取市场情绪数据时的错误处理"""
    mock_response = Mock()
    mock_response.text = '{"code": -1121, "msg": "Invalid symbol"}'
    mock_response.status_code = 400
    
    sentiment_service = MarketSentimentService()
    
    with patch.object(sentiment_service.binance, 'get_klines', 
                     side_effect=BinanceAPIException(
                         response=mock_response,
                         status_code=400,
                         text='{"code": -1121, "msg": "Invalid symbol"}'
                     )):
        with pytest.raises(BinanceAPIException):
            sentiment_service.get_crypto_sentiment('INVALID_PAIR')

def test_sentiment_calculation(service):
    """测试市场情绪计算逻辑"""
    sentiment_service = MarketSentimentService()
    
    # 测试不同情况下的情绪计算
    test_cases = [
        # 极度看多情况
        {
            'technical': {'rsi': 75, 'macd': {'histogram': 1.5}},
            'depth': {'pressure_ratio': 1.5},
            'volume': {'volume_score': 0.8, 'price_change_percent': 6},
            'whale': {'whale_activity_score': 0.7, 'whale_trades_count': 15}
        },
        # 看空情况
        {
            'technical': {'rsi': 25, 'macd': {'histogram': -1.5}},
            'depth': {'pressure_ratio': 0.7},
            'volume': {'volume_score': 0.3, 'price_change_percent': -6},
            'whale': {'whale_activity_score': 0.3, 'whale_trades_count': 5}
        }
    ]
    
    for case in test_cases:
        result = sentiment_service._calculate_overall_sentiment(
            case['technical'],
            case['depth'],
            case['volume'],
            case['whale']
        )
        
        assert 'score' in result
        assert 'label' in result
        assert 'details' in result
        assert 0 <= result['score'] <= 1 