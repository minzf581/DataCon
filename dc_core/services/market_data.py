"""
市场数据服务模块
提供基础的市场数据获取功能
"""
from typing import Dict, Optional
import logging
import yfinance as yf
from openbb import obb
from binance.client import Client
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

class MarketDataError(Exception):
    """市场数据错误基类"""
    pass

class DataSourceError(MarketDataError):
    """数据源错误"""
    pass

class MarketDataService:
    """市场数据服务"""
    
    def __init__(self):
        """初始化市场数据服务"""
        self.yf_client = yf.Ticker
        try:
            self.openbb = obb
        except Exception as e:
            logger.warning(f"OpenBB初始化失败: {e}")
            self.openbb = None
            
        try:
            self.binance = Client()
        except Exception as e:
            logger.warning(f"Binance初始化失败: {e}")
            self.binance = None
    
    def get_stock_data(self, symbol: str) -> Dict:
        """获取股票数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            包含股票数据的字典
            
        Raises:
            ValueError: 当股票代码为空时
            DataSourceError: 当无法从任何数据源获取数据时
        """
        if not symbol:
            logger.error("股票代码不能为空")
            raise ValueError("股票代码不能为空")
            
        try:
            # 首先尝试从 Yahoo Finance 获取数据
            data = self._get_yf_data(symbol)
            if data:
                return {'data': data, 'status': 'success'}
                
            # 如果 Yahoo Finance 失败，尝试从 OpenBB 获取数据
            data = self._get_openbb_data(symbol)
            if data:
                return {'data': data, 'status': 'success'}
                
            raise DataSourceError(f"无法从任何数据源获取{symbol}的数据")
        except Exception as e:
            logger.error(f"获取数据失败: {str(e)}")
            raise DataSourceError(str(e))
    
    def _get_yf_data(self, symbol: str) -> Optional[Dict]:
        """从Yahoo Finance获取数据"""
        try:
            ticker = self.yf_client(symbol)
            hist = ticker.history(period='1d')
            
            if hist.empty:
                logger.warning(f"Yahoo Finance未返回{symbol}的数据")
                return None
                
            return {
                'market_data': hist.to_dict('records'),
                'current_price': float(hist['Close'].iloc[-1]),
                'volume': int(hist['Volume'].iloc[-1]),
                'timestamp': hist.index[-1].isoformat(),
                'source': 'yahoo'
            }
            
        except Exception as e:
            logger.error(f"Yahoo Finance数据获取失败: {e}")
            return None
    
    def _get_openbb_data(self, symbol: str) -> Optional[Dict]:
        """从OpenBB获取数据"""
        try:
            if not self.openbb:
                return None
                
            data = self.openbb.stocks.load(symbol)
            if data is None:
                return None
                
            return {
                'market_data': data.to_dict('records') if not data.empty else [],
                'current_price': float(data['Close'].iloc[-1]) if not data.empty else 0.0,
                'volume': int(data['Volume'].iloc[-1]) if not data.empty else 0,
                'timestamp': data.index[-1].isoformat() if not data.empty else None,
                'source': 'openbb'
            }
            
        except Exception as e:
            logger.error(f"OpenBB数据获取失败: {e}")
            return None
            
    def get_crypto_data(self, symbol: str = 'BTCUSDT') -> Dict:
        """获取加密货币数据
        
        Args:
            symbol: 交易对,默认为 BTCUSDT
            
        Returns:
            包含加密货币数据的字典
            
        Raises:
            DataSourceError: 当无法从 Binance 获取数据时
        """
        try:
            if not self.binance:
                raise DataSourceError("Binance客户端未初始化")
                
            # 获取K线数据
            klines = self.binance.get_klines(
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_1DAY,
                limit=1
            )
            
            # 获取24小时价格统计
            ticker = self.binance.get_ticker(symbol=symbol)
            
            # 获取市场深度
            depth = self.binance.get_order_book(symbol=symbol, limit=2)
            
            data = {
                'market_data': {
                    'open': float(klines[0][1]),
                    'high': float(klines[0][2]),
                    'low': float(klines[0][3]),
                    'close': float(klines[0][4]),
                    'volume': float(klines[0][5]),
                    'timestamp': klines[0][0]
                },
                'current_price': float(ticker['lastPrice']),
                'price_change': float(ticker['priceChange']),
                'price_change_percent': float(ticker['priceChangePercent']),
                'market_depth': {
                    'bids': depth['bids'][:2],
                    'asks': depth['asks'][:2]
                },
                'source': 'binance'
            }
            
            return {'data': data, 'status': 'success'}
            
        except BinanceAPIException as e:
            logger.error(f"Binance API错误: {e}")
            raise DataSourceError(f"Binance API错误: {e}")
        except Exception as e:
            logger.error(f"获取加密货币数据失败: {e}")
            raise DataSourceError(str(e)) 