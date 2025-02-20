import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from openbb import obb
import logging
from functools import lru_cache
from binance.client import Client
from binance.exceptions import BinanceAPIException

# 配置日志
logger = logging.getLogger(__name__)

class DataSourceError(Exception):
    """数据源错误基类"""
    pass

class InvalidSourceError(DataSourceError):
    """无效的数据源错误"""
    pass

class DataRetrievalError(DataSourceError):
    """数据获取错误"""
    pass

class DataSourceManager:
    """
    数据源管理器
    负责管理和协调不同数据源的数据获取
    """
    
    def __init__(self):
        self.sources = {
            'binance': self._get_binance_data,  # 将Binance设为默认数据源
            'yahoo': self._get_yahoo_data,
            'openbb': self._get_openbb_data
        }
        # 初始化Binance客户端
        try:
            self.binance_client = Client()
            logger.info("Binance客户端初始化成功")
        except Exception as e:
            logger.error(f"Binance客户端初始化失败: {str(e)}")
            self.binance_client = None
        
    @lru_cache(maxsize=100)
    def get_market_data(self, symbol: str = 'BTCUSDT', interval: str = '1d', source: str = 'binance') -> Dict[str, Any]:
        """获取市场数据
        
        Args:
            symbol: 交易对代码，默认为BTCUSDT
            interval: 数据间隔 (1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M)
            source: 数据源，默认为binance
            
        Returns:
            包含市场数据的字典
        """
        try:
            if source not in self.sources:
                logger.error(f"请求了不支持的数据源: {source}")
                raise InvalidSourceError(f"不支持的数据源: {source}")
                
            logger.info(f"正在从{source}获取{symbol}的市场数据")
            data = self.sources[source](symbol, interval)
            return self._format_response(data)
            
        except InvalidSourceError:
            raise
        except Exception as e:
            logger.error(f"获取{symbol}的市场数据时发生错误: {str(e)}", exc_info=True)
            raise DataRetrievalError(f"获取市场数据失败: {str(e)}")
        
    def get_technical_indicators(self, symbol: str, indicator: str, period: int = 14) -> Dict[str, Any]:
        """计算技术指标
        
        Args:
            symbol: 股票代码
            indicator: 指标类型 (RSI, MACD, BBANDS)
            period: 计算周期
            
        Returns:
            包含技术指标数据的字典
            
        Raises:
            ValueError: 当指标类型不支持时
            DataRetrievalError: 当数据获取或计算失败时
        """
        try:
            logger.info(f"开始计算{symbol}的{indicator}指标")
            
            # 获取历史数据
            data = self.get_market_data(symbol)
            if not data.get('market_data'):
                raise DataRetrievalError("无法获取市场数据")
                
            df = pd.DataFrame(data['market_data'])
            if df.empty or 'Close' not in df.columns:
                raise DataRetrievalError("市场数据格式无效")
            
            # 计算指标
            if indicator.upper() == 'RSI':
                result = self._calculate_rsi(df, period)
            elif indicator.upper() == 'MACD':
                result = self._calculate_macd(df)
            elif indicator.upper() == 'BBANDS':
                result = self._calculate_bollinger_bands(df, period)
            else:
                raise ValueError(f"不支持的技术指标: {indicator}")
            
            logger.info(f"成功计算{symbol}的{indicator}指标")
            return self._format_response(result)
            
        except (ValueError, DataRetrievalError):
            raise
        except Exception as e:
            logger.error(f"计算{symbol}的{indicator}指标时发生错误: {str(e)}", exc_info=True)
            raise DataRetrievalError(f"技术指标计算失败: {str(e)}")
            
    def get_fundamental_data(self, symbol: str, data_type: str = 'financials') -> Dict[str, Any]:
        """获取基本面数据"""
        stock = yf.Ticker(symbol)
        
        if data_type == 'financials':
            data = stock.financials
        elif data_type == 'balance_sheet':
            data = stock.balance_sheet
        elif data_type == 'cash_flow':
            data = stock.cashflow
        else:
            raise ValueError(f"不支持的数据类型: {data_type}")
            
        # 将 DataFrame 转换为可序列化的字典
        result = {}
        for column in data.columns:
            result[str(column)] = {}
            for index in data.index:
                result[str(column)][str(index)] = self._clean_float_value(data[column][index])
                
        return {
            'data': result,
            'type': data_type,
            'columns': [str(col) for col in data.columns],
            'index': [str(idx) for idx in data.index]
        }
            
    def get_market_sentiment(self, symbol: str, period: int = 30) -> Dict[str, Any]:
        """分析市场情绪
        
        Args:
            symbol: 股票代码
            period: 分析周期（天数）
            
        Returns:
            包含市场情绪指标的字典，包括：
            - momentum: 动量
            - volatility: 波动率
            - trend: 趋势（Bullish/Bearish）
            - volume_trend: 成交量趋势
            - rsi_signal: RSI信号
            
        Raises:
            DataRetrievalError: 当数据获取或计算失败时
        """
        try:
            logger.info(f"开始分析{symbol}的市场情绪，周期={period}天")
            
            # 获取历史数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period)
            
            stock = yf.Ticker(symbol)
            hist = stock.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise DataRetrievalError(f"无法获取{symbol}的历史数据")
            
            # 计算价格动量
            returns = hist['Close'].pct_change()
            momentum = float(returns.mean())
            
            # 计算波动率
            volatility = float(returns.std())
            
            # 计算移动平均趋势
            sma_20 = hist['Close'].rolling(window=20).mean()
            sma_50 = hist['Close'].rolling(window=50).mean()
            trend = 'Bullish' if sma_20.iloc[-1] > sma_50.iloc[-1] else 'Bearish'
            
            # 计算成交量趋势
            volume_sma = hist['Volume'].rolling(window=20).mean()
            volume_trend = 'Increasing' if hist['Volume'].iloc[-1] > volume_sma.iloc[-1] else 'Decreasing'
            
            # 计算RSI信号
            rsi = self._calculate_rsi(hist, 14)['RSI'][-1]
            rsi_signal = 'Overbought' if rsi > 70 else 'Oversold' if rsi < 30 else 'Neutral'
            
            result = {
                'momentum': self._clean_float_value(momentum),
                'volatility': self._clean_float_value(volatility),
                'trend': trend,
                'volume_trend': volume_trend,
                'rsi_signal': rsi_signal,
                'period': period,
                'last_price': float(hist['Close'].iloc[-1]),
                'last_volume': int(hist['Volume'].iloc[-1]),
                'timestamp': hist.index[-1].isoformat(),
                'analysis_details': {
                    'sma_20': float(sma_20.iloc[-1]),
                    'sma_50': float(sma_50.iloc[-1]),
                    'rsi': float(rsi),
                    'volume_sma': float(volume_sma.iloc[-1])
                }
            }
            
            logger.info(f"成功分析{symbol}的市场情绪")
            return result
            
        except Exception as e:
            logger.error(f"分析{symbol}的市场情绪时发生错误: {str(e)}", exc_info=True)
            raise DataRetrievalError(f"市场情绪分析失败: {str(e)}")
        
    def get_available_sources(self) -> List[str]:
        """获取所有可用的数据源"""
        return list(self.sources.keys())
        
    def _get_yahoo_data(self, symbol: str, interval: str) -> pd.DataFrame:
        """从 Yahoo Finance 获取数据
        
        Args:
            symbol: 股票代码
            interval: 数据间隔 (1d, 1h, 15m等)
            
        Returns:
            包含市场数据的DataFrame
            
        Raises:
            DataRetrievalError: 当数据获取失败时
        """
        try:
            logger.info(f"正在从Yahoo Finance获取{symbol}的数据")
            
            # 获取股票对象
            stock = yf.Ticker(symbol)
            
            # 获取历史数据
            hist = stock.history(period='1y', interval=interval)
            if hist.empty:
                raise DataRetrievalError(f"Yahoo Finance未返回{symbol}的数据")
                
            # 获取公司信息
            try:
                info = stock.info
            except Exception as e:
                logger.warning(f"获取{symbol}的公司信息失败: {str(e)}")
                info = {}
                
            # 获取财务数据
            try:
                financials = stock.financials.to_dict() if not stock.financials.empty else {}
            except Exception as e:
                logger.warning(f"获取{symbol}的财务数据失败: {str(e)}")
                financials = {}
                
            # 合并数据
            result = {
                'market_data': hist.to_dict(),
                'info': info,
                'financials': financials
            }
            
            logger.info(f"成功获取{symbol}的Yahoo Finance数据")
            return self._format_response(result)
            
        except Exception as e:
            logger.error(f"从Yahoo Finance获取{symbol}数据失败: {str(e)}", exc_info=True)
            raise DataRetrievalError(f"从Yahoo Finance获取数据失败: {str(e)}")
        
    def _get_binance_data(self, symbol: str, interval: str) -> Dict[str, Any]:
        """从Binance获取数据
        
        Args:
            symbol: 交易对代码 (例如: BTCUSDT)
            interval: K线间隔
            
        Returns:
            包含市场数据的字典
        """
        try:
            if not self.binance_client:
                raise DataRetrievalError("Binance客户端未初始化")
                
            # 获取K线数据
            klines = self.binance_client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=100  # 最近100条数据
            )
            
            # 获取24小时价格统计
            ticker_24h = self.binance_client.get_ticker(symbol=symbol)
            
            # 获取市场深度
            depth = self.binance_client.get_order_book(symbol=symbol)
            
            # 转换K线数据为DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # 格式化数据
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
                
            result = {
                'market_data': df.to_dict('records'),
                'current_price': float(ticker_24h['lastPrice']),
                'price_change_24h': float(ticker_24h['priceChange']),
                'price_change_percent_24h': float(ticker_24h['priceChangePercent']),
                'volume_24h': float(ticker_24h['volume']),
                'high_24h': float(ticker_24h['highPrice']),
                'low_24h': float(ticker_24h['lowPrice']),
                'market_depth': {
                    'bids': depth['bids'][:5],  # 前5档买单
                    'asks': depth['asks'][:5]   # 前5档卖单
                },
                'timestamp': datetime.now().isoformat(),
                'source': 'binance'
            }
            
            return result
            
        except BinanceAPIException as e:
            logger.error(f"Binance API错误: {str(e)}")
            raise DataRetrievalError(f"Binance数据获取失败: {str(e)}")
        except Exception as e:
            logger.error(f"获取Binance数据时发生错误: {str(e)}")
            raise DataRetrievalError(str(e))
        
    def _get_openbb_data(self, symbol: str, interval: str) -> pd.DataFrame:
        """从OpenBB获取数据
        
        Args:
            symbol: 股票代码
            interval: 数据间隔
            
        Returns:
            包含市场数据、基本面数据和技术指标的DataFrame
            
        Raises:
            DataRetrievalError: 当数据获取失败时
        """
        try:
            logger.info(f"正在从OpenBB获取{symbol}的数据")
            
            # 获取股票数据
            data = obb.stocks.load(symbol)
            if data is None or data.empty:
                raise DataRetrievalError(f"OpenBB未返回{symbol}的市场数据")
            
            # 获取基本面数据
            try:
                fundamentals = obb.stocks.fundamentals(symbol)
            except Exception as e:
                logger.warning(f"获取{symbol}的基本面数据失败: {str(e)}")
                fundamentals = pd.DataFrame()
            
            # 获取技术指标
            try:
                technicals = obb.stocks.technical_indicators(symbol)
            except Exception as e:
                logger.warning(f"获取{symbol}的技术指标失败: {str(e)}")
                technicals = pd.DataFrame()
            
            # 合并数据
            result = {
                'market_data': data.to_dict(),
                'fundamentals': fundamentals.to_dict() if not fundamentals.empty else {},
                'technicals': technicals.to_dict() if not technicals.empty else {}
            }
            
            logger.info(f"成功获取{symbol}的OpenBB数据")
            return self._format_response(result)
            
        except Exception as e:
            logger.error(f"从OpenBB获取{symbol}数据失败: {str(e)}", exc_info=True)
            raise DataRetrievalError(f"从OpenBB获取数据失败: {str(e)}")
        
    def _calculate_rsi(self, df: pd.DataFrame, period: int) -> Dict[str, Any]:
        """计算 RSI 指标
        
        Args:
            df: 包含价格数据的DataFrame
            period: RSI计算周期
            
        Returns:
            包含RSI值的字典
        """
        try:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return {
                'RSI': self._clean_float_values(rsi.values.tolist()),
                'period': period,
                'timestamp': df.index.tolist()
            }
        except Exception as e:
            logger.error(f"RSI计算失败: {str(e)}")
            raise DataRetrievalError(f"RSI计算失败: {str(e)}")
        
    def _calculate_macd(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算 MACD 指标
        
        Args:
            df: 包含价格数据的DataFrame
            
        Returns:
            包含MACD、Signal和Histogram的字典
        """
        try:
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            histogram = macd - signal
            
            return {
                'MACD': self._clean_float_values(macd.values.tolist()),
                'Signal': self._clean_float_values(signal.values.tolist()),
                'Histogram': self._clean_float_values(histogram.values.tolist()),
                'timestamp': df.index.tolist()
            }
        except Exception as e:
            logger.error(f"MACD计算失败: {str(e)}")
            raise DataRetrievalError(f"MACD计算失败: {str(e)}")
        
    def _calculate_bollinger_bands(self, df: pd.DataFrame, period: int) -> Dict[str, Any]:
        """计算布林带指标
        
        Args:
            df: 包含价格数据的DataFrame
            period: 计算周期
            
        Returns:
            包含中轨、上轨和下轨的字典
        """
        try:
            sma = df['Close'].rolling(window=period).mean()
            std = df['Close'].rolling(window=period).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            return {
                'Middle': self._clean_float_values(sma.values.tolist()),
                'Upper': self._clean_float_values(upper_band.values.tolist()),
                'Lower': self._clean_float_values(lower_band.values.tolist()),
                'period': period,
                'timestamp': df.index.tolist()
            }
        except Exception as e:
            logger.error(f"布林带计算失败: {str(e)}")
            raise DataRetrievalError(f"布林带计算失败: {str(e)}")
        
    def _format_response(self, data: Any) -> Dict[str, Any]:
        """格式化响应数据
        
        Args:
            data: 原始数据
            
        Returns:
            格式化后的数据字典
        """
        if isinstance(data, pd.DataFrame):
            formatted_data = {
                'data': {
                    'market_data': data.to_dict('records'),
                    'current_price': float(data['Close'].iloc[-1]) if 'Close' in data else None,
                    'volume': float(data['Volume'].iloc[-1]) if 'Volume' in data else None,
                    'timestamp': data.index[-1].isoformat() if isinstance(data.index[-1], pd.Timestamp) else None,
                    'source': 'yahoo'
                },
                'type': 'dataframe'
            }
        elif isinstance(data, dict):
            formatted_data = {
                'data': data,
                'type': 'dict'
            }
        else:
            formatted_data = {
                'data': str(data),
                'type': 'string'
            }
            
        return formatted_data
            
    def _clean_float_values(self, values: List[float]) -> List[float]:
        """清理浮点数值列表"""
        return [self._clean_float_value(x) for x in values]
        
    def _clean_float_value(self, value: float) -> float:
        """清理单个浮点数值"""
        if pd.isna(value) or np.isinf(value):
            return 0.0
        return float(value) 