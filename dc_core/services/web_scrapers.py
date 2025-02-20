from typing import Dict, List, Any
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import aiohttp
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import json
import logging
from fake_useragent import UserAgent
from .anti_crawler import AntiCrawler

logger = logging.getLogger(__name__)

class MarketSentimentScraper:
    """市场情绪数据爬虫"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.anti_crawler = AntiCrawler(redis_url)
        self.headers = {'User-Agent': UserAgent().random}
        self.session = requests.Session()
        
    async def get_social_sentiment(self, symbol: str) -> Dict:
        """获取社交媒体情绪数据
        
        来源：
        - Twitter
        - Reddit
        - StockTwits
        """
        tasks = [
            self._get_twitter_sentiment(symbol),
            self._get_reddit_sentiment(symbol),
            self._get_stocktwits_sentiment(symbol)
        ]
        results = await asyncio.gather(*tasks)
        
        return {
            'twitter': results[0],
            'reddit': results[1],
            'stocktwits': results[2]
        }
        
    async def get_news_sentiment(self, symbol: str) -> Dict:
        """获取新闻情绪数据
        
        来源：
        - 雪球
        - 东方财富
        - 新浪财经
        """
        tasks = [
            self._get_xueqiu_news(symbol),
            self._get_eastmoney_news(symbol),
            self._get_sina_news(symbol)
        ]
        results = await asyncio.gather(*tasks)
        
        return {
            'xueqiu': results[0],
            'eastmoney': results[1],
            'sina': results[2]
        }
        
    async def _get_twitter_sentiment(self, symbol: str) -> Dict:
        """获取 Twitter 情绪数据"""
        try:
            url = f"https://api.twitter.com/2/tweets/search/recent?query=${symbol}"
            data = await self.anti_crawler.make_request(url)
            if data:
                return self._analyze_tweets(data)
            return {}
        except Exception as e:
            logger.error(f"获取Twitter数据失败: {str(e)}")
            return {}
            
    async def _get_reddit_sentiment(self, symbol: str) -> Dict:
        """获取 Reddit 情绪数据"""
        try:
            subreddits = ['wallstreetbets', 'stocks', 'investing']
            all_posts = []
            
            for subreddit in subreddits:
                url = f"https://www.reddit.com/r/{subreddit}/search.json"
                params = {
                    'q': symbol,
                    't': 'day',
                    'sort': 'top'
                }
                data = await self.anti_crawler.make_request(url, params=params)
                if data:
                    posts = data.get('data', {}).get('children', [])
                    all_posts.extend(posts)
                    
            return self._analyze_reddit_posts(all_posts)
        except Exception as e:
            logger.error(f"获取Reddit数据失败: {str(e)}")
            return {}
            
    async def _get_stocktwits_sentiment(self, symbol: str) -> Dict:
        """获取 StockTwits 情绪数据"""
        try:
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
            data = await self.anti_crawler.make_request(url)
            if data:
                return self._analyze_stocktwits(data)
            return {}
        except Exception as e:
            logger.error(f"获取StockTwits数据失败: {str(e)}")
            return {}
            
    async def _get_xueqiu_news(self, symbol: str) -> Dict:
        """获取雪球新闻数据"""
        try:
            # 处理股票代码格式
            if '.' in symbol:
                code = symbol.split('.')[0]
            else:
                code = symbol
                
            url = f"https://xueqiu.com/S/{code}"
            html = await self.anti_crawler.make_request(url)
            if html:
                # 使用BeautifulSoup解析HTML
                soup = BeautifulSoup(html, 'lxml')
                
                news_elements = soup.find_all('div', class_='timeline__item')
                news_data = []
                
                for element in news_elements[:10]:
                    try:
                        title = element.find('div', class_='timeline__title').text.strip()
                        time = element.find('div', class_='timeline__time').text.strip()
                        news_data.append({
                            'title': title,
                            'time': time
                        })
                    except:
                        continue
                        
                return {
                    'news_count': len(news_data),
                    'news': news_data
                }
            return {}
        except Exception as e:
            logger.error(f"获取雪球数据失败: {str(e)}")
            return {}
            
    async def _get_eastmoney_news(self, symbol: str) -> Dict:
        """获取东方财富新闻数据"""
        try:
            url = f"http://guba.eastmoney.com/list,{symbol}.html"
            html = await self.anti_crawler.make_request(url)
            if html:
                soup = BeautifulSoup(html, 'lxml')
                
                news_list = soup.find_all('div', class_='article-list')
                news_data = []
                
                for news in news_list[:10]:
                    try:
                        title = news.find('a', class_='title').text.strip()
                        time = news.find('span', class_='time').text.strip()
                        news_data.append({
                            'title': title,
                            'time': time
                        })
                    except:
                        continue
                        
                return {
                    'news_count': len(news_data),
                    'news': news_data
                }
            return {}
        except Exception as e:
            logger.error(f"获取东方财富数据失败: {str(e)}")
            return {}
            
    async def _get_sina_news(self, symbol: str) -> Dict:
        """获取新浪财经新闻数据"""
        try:
            url = f"https://vip.stock.finance.sina.com.cn/corp/go.php/vCB_AllNewsStock/symbol/{symbol}.phtml"
            html = await self.anti_crawler.make_request(url)
            if html:
                soup = BeautifulSoup(html, 'lxml')
                
                news_list = soup.find_all('div', class_='datelist')
                news_data = []
                
                for news in news_list[:10]:
                    try:
                        title = news.find('a').text.strip()
                        time = news.find('span').text.strip()
                        news_data.append({
                            'title': title,
                            'time': time
                        })
                    except:
                        continue
                        
                return {
                    'news_count': len(news_data),
                    'news': news_data
                }
            return {}
        except Exception as e:
            logger.error(f"获取新浪财经数据失败: {str(e)}")
            return {}
            
    def _analyze_tweets(self, data: Dict) -> Dict:
        """分析 Twitter 数据"""
        tweets = data.get('data', [])
        
        # 简单的情绪分析
        positive_keywords = ['buy', 'bullish', 'long', 'up', 'good', 'great']
        negative_keywords = ['sell', 'bearish', 'short', 'down', 'bad', 'poor']
        
        sentiment_scores = []
        for tweet in tweets:
            text = tweet.get('text', '').lower()
            score = 0
            for word in positive_keywords:
                if word in text:
                    score += 1
            for word in negative_keywords:
                if word in text:
                    score -= 1
            sentiment_scores.append(score)
            
        return {
            'tweet_count': len(tweets),
            'average_sentiment': sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0,
            'positive_count': len([s for s in sentiment_scores if s > 0]),
            'negative_count': len([s for s in sentiment_scores if s < 0]),
            'neutral_count': len([s for s in sentiment_scores if s == 0])
        }
        
    def _analyze_reddit_posts(self, posts: List) -> Dict:
        """分析 Reddit 帖子"""
        sentiment_data = {
            'post_count': len(posts),
            'total_score': 0,
            'total_comments': 0,
            'sentiment_distribution': {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            }
        }
        
        for post in posts:
            post_data = post.get('data', {})
            sentiment_data['total_score'] += post_data.get('score', 0)
            sentiment_data['total_comments'] += post_data.get('num_comments', 0)
            
            # 基于标题的简单情绪分析
            title = post_data.get('title', '').lower()
            if any(word in title for word in ['buy', 'bullish', 'long']):
                sentiment_data['sentiment_distribution']['positive'] += 1
            elif any(word in title for word in ['sell', 'bearish', 'short']):
                sentiment_data['sentiment_distribution']['negative'] += 1
            else:
                sentiment_data['sentiment_distribution']['neutral'] += 1
                
        return sentiment_data
        
    def _analyze_stocktwits(self, data: Dict) -> Dict:
        """分析 StockTwits 数据"""
        messages = data.get('messages', [])
        
        sentiment_data = {
            'message_count': len(messages),
            'sentiment_distribution': {
                'bullish': 0,
                'bearish': 0,
                'neutral': 0
            }
        }
        
        for message in messages:
            sentiment = message.get('entities', {}).get('sentiment', {}).get('basic', '')
            if sentiment == 'Bullish':
                sentiment_data['sentiment_distribution']['bullish'] += 1
            elif sentiment == 'Bearish':
                sentiment_data['sentiment_distribution']['bearish'] += 1
            else:
                sentiment_data['sentiment_distribution']['neutral'] += 1
                
        return sentiment_data

class TradeDataScraper:
    """交易数据爬虫"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.anti_crawler = AntiCrawler(redis_url)
        self.headers = {'User-Agent': UserAgent().random}
        
    async def get_trade_data(self, symbol: str) -> Dict:
        """获取交易数据
        
        来源：
        - Level 2 数据
        - 大单交易
        - 龙虎榜
        """
        tasks = [
            self._get_level2_data(symbol),
            self._get_big_deals(symbol),
            self._get_top_traders(symbol)
        ]
        results = await asyncio.gather(*tasks)
        
        return {
            'level2': results[0],
            'big_deals': results[1],
            'top_traders': results[2]
        }
        
    async def _get_level2_data(self, symbol: str) -> Dict:
        """获取 Level 2 数据"""
        try:
            url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={symbol}&fields=f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58"
            data = await self.anti_crawler.make_request(url)
            if data:
                return self._parse_level2_data(data)
            return {}
        except Exception as e:
            logger.error(f"获取Level2数据失败: {str(e)}")
            return {}
            
    async def _get_big_deals(self, symbol: str) -> Dict:
        """获取大单交易数据"""
        try:
            url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={symbol}&fields=f19,f20,f21,f22"
            data = await self.anti_crawler.make_request(url)
            if data:
                return self._parse_big_deals(data)
            return {}
        except Exception as e:
            logger.error(f"获取大单数据失败: {str(e)}")
            return {}
            
    async def _get_top_traders(self, symbol: str) -> Dict:
        """获取龙虎榜数据"""
        try:
            url = f"http://data.eastmoney.com/stock/lhb,{symbol}.html"
            html = await self.anti_crawler.make_request(url)
            if html:
                soup = BeautifulSoup(html, 'lxml')
                
                # 获取买入和卖出前5名
                buy_elements = soup.select(".tab1 tr")
                sell_elements = soup.select(".tab2 tr")
                
                buy_data = []
                sell_data = []
                
                # 解析买入数据
                for element in buy_elements[1:6]:  # 跳过表头
                    try:
                        cols = element.find_all("td")
                        buy_data.append({
                            'trader_name': cols[1].text.strip(),
                            'buy_amount': cols[2].text.strip(),
                            'buy_ratio': cols[3].text.strip()
                        })
                    except:
                        continue
                        
                # 解析卖出数据
                for element in sell_elements[1:6]:  # 跳过表头
                    try:
                        cols = element.find_all("td")
                        sell_data.append({
                            'trader_name': cols[1].text.strip(),
                            'sell_amount': cols[2].text.strip(),
                            'sell_ratio': cols[3].text.strip()
                        })
                    except:
                        continue
                        
                return {
                    'buy_data': buy_data,
                    'sell_data': sell_data
                }
            return {}
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败: {str(e)}")
            return {}
            
    def _parse_level2_data(self, data: Dict) -> Dict:
        """解析 Level 2 数据"""
        try:
            result = {
                'buy_orders': [],
                'sell_orders': []
            }
            
            # 解析买单
            for i in range(10):
                price_key = f'f{47+i}'
                volume_key = f'f{57+i}'
                if price_key in data and volume_key in data:
                    result['buy_orders'].append({
                        'price': data[price_key],
                        'volume': data[volume_key]
                    })
                    
            return result
        except Exception as e:
            logger.error(f"解析Level2数据失败: {str(e)}")
            return {}
            
    def _parse_big_deals(self, data: Dict) -> Dict:
        """解析大单交易数据"""
        try:
            return {
                'big_buy_count': data.get('f19', 0),
                'big_buy_amount': data.get('f20', 0),
                'big_sell_count': data.get('f21', 0),
                'big_sell_amount': data.get('f22', 0)
            }
        except Exception as e:
            logger.error(f"解析大单数据失败: {str(e)}")
            return {} 