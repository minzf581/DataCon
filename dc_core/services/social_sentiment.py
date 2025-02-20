import os
import logging
import asyncio
from typing import Dict, List, Optional
import tweepy
from dotenv import load_dotenv
from datetime import datetime, timedelta

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

class SocialSentimentService:
    """社交媒体情绪分析服务"""
    
    def __init__(self):
        """初始化Twitter客户端"""
        self.twitter_client = self._init_twitter_client()
        self._last_twitter_request = datetime.min
        self._twitter_rate_limit = 2.0  # 每2秒最多1个请求
        
    def _init_twitter_client(self) -> Optional[tweepy.Client]:
        """初始化Twitter客户端"""
        try:
            if not all([
                os.getenv('TWITTER_BEARER_TOKEN'),
                os.getenv('TWITTER_API_KEY'),
                os.getenv('TWITTER_API_SECRET'),
                os.getenv('TWITTER_ACCESS_TOKEN'),
                os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
            ]):
                logger.warning("Twitter API凭证未完全配置")
                return None
                
            return tweepy.Client(
                bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
                consumer_key=os.getenv('TWITTER_API_KEY'),
                consumer_secret=os.getenv('TWITTER_API_SECRET'),
                access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
                access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
                wait_on_rate_limit=True
            )
        except Exception as e:
            logger.error(f"Twitter客户端初始化失败: {e}")
            return None
            
    async def get_social_sentiment(self, symbol: str) -> Dict:
        """获取社交媒体情绪数据
        
        Args:
            symbol: 股票/加密货币代码
            
        Returns:
            包含Twitter情绪数据的字典
        """
        try:
            # 获取Twitter数据
            twitter_data = None
            if self.twitter_client:
                twitter_data = await self._get_twitter_sentiment(symbol)
            
            # 汇总数据
            sentiment_data = {
                'twitter': twitter_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # 计算综合情绪
            overall_sentiment = self._calculate_overall_sentiment(sentiment_data)
            sentiment_data['overall'] = overall_sentiment
            
            return {'data': sentiment_data, 'status': 'success'}
            
        except Exception as e:
            logger.error(f"获取社交媒体情绪数据失败: {e}")
            return {'error': str(e), 'status': 'error'}
            
    async def _get_twitter_sentiment(self, symbol: str) -> Optional[Dict]:
        """获取Twitter情绪数据"""
        try:
            if not self.twitter_client:
                return None
                
            # 实现简单的速率限制
            now = datetime.now()
            time_since_last_request = (now - self._last_twitter_request).total_seconds()
            if time_since_last_request < self._twitter_rate_limit:
                await asyncio.sleep(self._twitter_rate_limit - time_since_last_request)
            
            # 搜索相关推文
            query = f"{symbol} (crypto OR bitcoin OR cryptocurrency) lang:en -is:retweet"
            tweets = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=20,  # 减少请求数量
                tweet_fields=['created_at', 'public_metrics']
            )
            
            self._last_twitter_request = datetime.now()
            
            if not tweets.data:
                return None
                
            # 分析推文情绪
            return {
                'tweet_count': len(tweets.data),
                'metrics': self._analyze_tweets(tweets.data),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取Twitter数据失败: {e}")
            return None
            
    def _analyze_tweets(self, tweets: List) -> Dict:
        """分析推文情绪"""
        sentiment_counts = {
            'bullish': 0,
            'bearish': 0,
            'neutral': 0
        }
        
        # 扩展关键词列表
        bullish_keywords = [
            'buy', 'long', 'bullish', 'moon', 'pump',
            'hodl', 'hold', 'up', 'rise', 'rising',
            'gain', 'profit', 'bull', 'breakout'
        ]
        bearish_keywords = [
            'sell', 'short', 'bearish', 'dump', 'crash',
            'down', 'fall', 'falling', 'loss', 'bear',
            'breakdown', 'correction', 'dip'
        ]
        
        for tweet in tweets:
            text = tweet.text.lower()
            
            bullish_count = sum(1 for word in bullish_keywords if word in text)
            bearish_count = sum(1 for word in bearish_keywords if word in text)
            
            if bullish_count > bearish_count:
                sentiment_counts['bullish'] += 1
            elif bearish_count > bullish_count:
                sentiment_counts['bearish'] += 1
            else:
                sentiment_counts['neutral'] += 1
                
        total = sum(sentiment_counts.values())
        
        return {
            'sentiment_counts': sentiment_counts,
            'sentiment_ratio': {
                'bullish': sentiment_counts['bullish'] / total if total > 0 else 0,
                'bearish': sentiment_counts['bearish'] / total if total > 0 else 0,
                'neutral': sentiment_counts['neutral'] / total if total > 0 else 0
            }
        }
        
    def _calculate_overall_sentiment(self, data: Dict) -> Dict:
        """计算综合情绪指标"""
        if not data['twitter']:
            return {
                'score': 0.5,
                'label': '数据不足',
                'confidence': 0
            }
            
        # 使用Twitter数据计算情绪
        metrics = data['twitter']['metrics']
        ratios = metrics['sentiment_ratio']
        
        # 计算情绪评分 (0-1, 0.5为中性)
        sentiment_score = ratios['bullish'] / (ratios['bullish'] + ratios['bearish']) if (ratios['bullish'] + ratios['bearish']) > 0 else 0.5
        
        # 确定情绪标签
        if sentiment_score > 0.6:
            label = '看多'
        elif sentiment_score < 0.4:
            label = '看空'
        else:
            label = '中性'
            
        # 计算置信度
        confidence = 1 - ratios['neutral']
        
        return {
            'score': sentiment_score,
            'label': label,
            'confidence': confidence
        }
        
    async def close(self):
        """关闭资源"""
        pass  # 不再需要关闭任何资源 