from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging

logger = logging.getLogger(__name__)

class MarketSentimentService:
    """市场情绪分析服务"""
    
    def __init__(self):
        """初始化市场情绪服务"""
        try:
            self.binance = Client()
        except Exception as e:
            logger.error(f"Binance客户端初始化失败: {e}")
            self.binance = None
            
    def get_crypto_sentiment(self, symbol: str = 'BTCUSDT') -> Dict:
        """获取加密货币市场情绪数据
        
        Args:
            symbol: 交易对代码,默认为BTCUSDT
            
        Returns:
            Dict: 包含市场情绪指标的字典
        """
        try:
            # 获取技术指标
            technical_indicators = self._get_technical_indicators(symbol)
            
            # 获取市场深度数据
            market_depth = self._get_market_depth_analysis(symbol)
            
            # 获取交易量分析
            volume_analysis = self._get_volume_analysis(symbol)
            
            # 获取大额交易信息
            whale_analysis = self._get_whale_analysis(symbol)
            
            # 汇总市场情绪
            sentiment = self._calculate_overall_sentiment(
                technical_indicators,
                market_depth,
                volume_analysis,
                whale_analysis
            )
            
            return {
                'status': 'success',
                'data': {
                    'timestamp': datetime.now().isoformat(),
                    'symbol': symbol,
                    'sentiment_score': sentiment['score'],
                    'sentiment_label': sentiment['label'],
                    'technical_analysis': technical_indicators,
                    'market_depth': market_depth,
                    'volume_analysis': volume_analysis,
                    'whale_activity': whale_analysis,
                    'details': sentiment['details']
                }
            }
            
        except Exception as e:
            logger.error(f"获取市场情绪数据失败: {e}")
            raise
            
    def _get_technical_indicators(self, symbol: str) -> Dict:
        """获取技术指标"""
        try:
            # 获取K线数据
            klines = self.binance.get_klines(
                symbol=symbol,
                interval=Client.KLINE_INTERVAL_1HOUR,
                limit=24  # 24小时数据
            )
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 
                'volume', 'close_time', 'quote_volume', 'trades',
                'taker_base', 'taker_quote', 'ignore'
            ])
            
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # 计算RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 计算MACD
            exp1 = df['close'].ewm(span=12, adjust=False).mean()
            exp2 = df['close'].ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9, adjust=False).mean()
            
            # 计算布林带
            sma = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            
            current_price = float(df['close'].iloc[-1])
            
            return {
                'rsi': float(rsi.iloc[-1]),
                'macd': {
                    'macd': float(macd.iloc[-1]),
                    'signal': float(signal.iloc[-1]),
                    'histogram': float(macd.iloc[-1] - signal.iloc[-1])
                },
                'bollinger_bands': {
                    'upper': float(upper_band.iloc[-1]),
                    'middle': float(sma.iloc[-1]),
                    'lower': float(lower_band.iloc[-1]),
                    'current_price': current_price,
                    'position': self._get_bb_position(
                        current_price,
                        float(upper_band.iloc[-1]),
                        float(lower_band.iloc[-1])
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"获取技术指标失败: {e}")
            return {}
            
    def _get_market_depth_analysis(self, symbol: str) -> Dict:
        """分析市场深度"""
        try:
            depth = self.binance.get_order_book(symbol=symbol, limit=20)
            
            bids = pd.DataFrame(depth['bids'], columns=['price', 'quantity'], dtype=float)
            asks = pd.DataFrame(depth['asks'], columns=['price', 'quantity'], dtype=float)
            
            bid_sum = (bids['price'] * bids['quantity']).sum()
            ask_sum = (asks['price'] * asks['quantity']).sum()
            
            return {
                'buy_pressure': float(bid_sum),
                'sell_pressure': float(ask_sum),
                'pressure_ratio': float(bid_sum / ask_sum if ask_sum > 0 else 1),
                'spread': float(asks['price'].iloc[0] - bids['price'].iloc[0]),
                'depth_score': self._calculate_depth_score(bids, asks)
            }
            
        except Exception as e:
            logger.error(f"获取市场深度分析失败: {e}")
            return {}
            
    def _get_volume_analysis(self, symbol: str) -> Dict:
        """分析交易量"""
        try:
            # 获取24小时统计数据
            ticker = self.binance.get_ticker(symbol=symbol)
            
            return {
                'volume_24h': float(ticker['volume']),
                'quote_volume_24h': float(ticker['quoteVolume']),
                'price_change_percent': float(ticker['priceChangePercent']),
                'trades_24h': int(ticker['count']),
                'volume_score': self._calculate_volume_score(ticker)
            }
            
        except Exception as e:
            logger.error(f"获取交易量分析失败: {e}")
            return {}
            
    def _get_whale_analysis(self, symbol: str) -> Dict:
        """分析大户活动"""
        try:
            # 获取最近的大额交易
            trades = self.binance.get_recent_trades(symbol=symbol, limit=100)
            
            # 筛选大额交易
            threshold = self._calculate_whale_threshold(trades)
            whale_trades = [t for t in trades if float(t['quoteQty']) > threshold]
            
            return {
                'whale_trades_count': len(whale_trades),
                'total_whale_volume': sum(float(t['quoteQty']) for t in whale_trades),
                'avg_whale_trade_size': sum(float(t['quoteQty']) for t in whale_trades) / len(whale_trades) if whale_trades else 0,
                'whale_activity_score': self._calculate_whale_score(whale_trades, trades)
            }
            
        except Exception as e:
            logger.error(f"获取大户分析失败: {e}")
            return {}
            
    def _calculate_overall_sentiment(self, technical: Dict, depth: Dict, 
                                   volume: Dict, whale: Dict) -> Dict:
        """计算整体市场情绪"""
        scores = []
        details = []
        
        # 技术指标评分
        if technical:
            rsi = technical.get('rsi', 50)
            if rsi > 70:
                details.append("RSI显示超买")
            elif rsi < 30:
                details.append("RSI显示超卖")
            
            macd = technical.get('macd', {})
            if macd.get('histogram', 0) > 0:
                details.append("MACD显示上升趋势")
            else:
                details.append("MACD显示下降趋势")
                
            scores.append(self._normalize_rsi(rsi))
            
        # 市场深度评分
        if depth:
            pressure_ratio = depth.get('pressure_ratio', 1)
            if pressure_ratio > 1.2:
                details.append("买方压力明显")
            elif pressure_ratio < 0.8:
                details.append("卖方压力明显")
                
            scores.append(self._normalize_pressure_ratio(pressure_ratio))
            
        # 交易量评分
        if volume:
            volume_score = volume.get('volume_score', 0.5)
            scores.append(volume_score)
            
            if volume.get('price_change_percent', 0) > 5:
                details.append("价格大幅上涨")
            elif volume.get('price_change_percent', 0) < -5:
                details.append("价格大幅下跌")
                
        # 大户活动评分
        if whale:
            whale_score = whale.get('whale_activity_score', 0.5)
            scores.append(whale_score)
            
            if whale.get('whale_trades_count', 0) > 10:
                details.append("大户活动频繁")
                
        # 计算综合得分
        final_score = np.mean(scores) if scores else 0.5
        
        # 确定情绪标签
        if final_score >= 0.7:
            sentiment = "非常看多"
        elif final_score >= 0.6:
            sentiment = "看多"
        elif final_score >= 0.4:
            sentiment = "中性"
        elif final_score >= 0.3:
            sentiment = "看空"
        else:
            sentiment = "非常看空"
            
        return {
            'score': float(final_score),
            'label': sentiment,
            'details': details
        }
        
    def _get_bb_position(self, price: float, upper: float, lower: float) -> str:
        """判断价格在布林带中的位置"""
        if price >= upper:
            return "超买"
        elif price <= lower:
            return "超卖"
        else:
            return "区间内"
            
    def _calculate_depth_score(self, bids: pd.DataFrame, asks: pd.DataFrame) -> float:
        """计算市场深度得分"""
        bid_sum = (bids['price'] * bids['quantity']).sum()
        ask_sum = (asks['price'] * asks['quantity']).sum()
        
        ratio = bid_sum / ask_sum if ask_sum > 0 else 1
        return self._normalize_pressure_ratio(ratio)
        
    def _calculate_volume_score(self, ticker: Dict) -> float:
        """计算交易量得分"""
        try:
            volume = float(ticker['volume'])
            avg_volume = float(ticker['weightedAvgPrice']) * volume
            
            # 根据成交量相对于平均值的比例计算得分
            ratio = volume / avg_volume if avg_volume > 0 else 1
            return self._normalize_ratio(ratio, 0.5, 2)
            
        except Exception:
            return 0.5
            
    def _calculate_whale_score(self, whale_trades: List, all_trades: List) -> float:
        """计算大户活动得分"""
        if not all_trades:
            return 0.5
            
        whale_volume = sum(float(t['quoteQty']) for t in whale_trades)
        total_volume = sum(float(t['quoteQty']) for t in all_trades)
        
        ratio = whale_volume / total_volume if total_volume > 0 else 0
        return self._normalize_ratio(ratio, 0.1, 0.5)
        
    def _calculate_whale_threshold(self, trades: List) -> float:
        """计算大户交易阈值"""
        if not trades:
            return 0
            
        volumes = [float(t['quoteQty']) for t in trades]
        return np.percentile(volumes, 90)  # 取90分位数作为阈值
        
    def _normalize_rsi(self, rsi: float) -> float:
        """标准化RSI值为0-1分数"""
        if rsi >= 70:
            return 0.8  # 超买
        elif rsi <= 30:
            return 0.2  # 超卖
        else:
            return 0.5 + (rsi - 50) / 100  # 线性映射到0.5附近
            
    def _normalize_pressure_ratio(self, ratio: float) -> float:
        """标准化压力比率为0-1分数"""
        return self._normalize_ratio(ratio, 0.5, 2)
        
    def _normalize_ratio(self, ratio: float, min_ratio: float, max_ratio: float) -> float:
        """将比率标准化到0-1范围"""
        if ratio <= min_ratio:
            return 0
        elif ratio >= max_ratio:
            return 1
        else:
            return (ratio - min_ratio) / (max_ratio - min_ratio) 