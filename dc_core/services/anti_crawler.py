import random
import time
import json
import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Union
from fake_useragent import UserAgent
import redis
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class ProxyPool:
    """代理池管理"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
        self.proxy_key = "proxy_pool"
        self.score_key = "proxy_scores"
        self.check_interval = 300  # 5分钟检查一次代理可用性
        self._start_checker()
        
    def _start_checker(self):
        """启动代理检查器"""
        checker_thread = threading.Thread(target=self._check_proxies_periodically)
        checker_thread.daemon = True
        checker_thread.start()
        
    def add_proxy(self, proxy: str, score: float = 10.0):
        """添加代理"""
        self.redis_client.sadd(self.proxy_key, proxy)
        self.redis_client.hset(self.score_key, proxy, score)
        
    def remove_proxy(self, proxy: str):
        """移除代理"""
        self.redis_client.srem(self.proxy_key, proxy)
        self.redis_client.hdel(self.score_key, proxy)
        
    def get_proxy(self) -> Optional[str]:
        """获取代理"""
        proxies = self.redis_client.smembers(self.proxy_key)
        if not proxies:
            self._fetch_new_proxies()
            proxies = self.redis_client.smembers(self.proxy_key)
            
        if not proxies:
            return None
            
        # 按分数排序选择代理
        proxy_scores = [(proxy, float(self.redis_client.hget(self.score_key, proxy) or 0))
                       for proxy in proxies]
        proxy_scores.sort(key=lambda x: x[1], reverse=True)
        
        return proxy_scores[0][0] if proxy_scores else None
        
    def update_score(self, proxy: str, success: bool):
        """更新代理分数"""
        current_score = float(self.redis_client.hget(self.score_key, proxy) or 10.0)
        if success:
            new_score = min(current_score + 1, 100)
        else:
            new_score = max(current_score - 2, 0)
            
        if new_score == 0:
            self.remove_proxy(proxy)
        else:
            self.redis_client.hset(self.score_key, proxy, new_score)
            
    def _check_proxies_periodically(self):
        """定期检查代理可用性"""
        while True:
            proxies = self.redis_client.smembers(self.proxy_key)
            with ThreadPoolExecutor(max_workers=10) as executor:
                executor.map(self._check_proxy, proxies)
            time.sleep(self.check_interval)
            
    def _check_proxy(self, proxy: str):
        """检查单个代理的可用性"""
        try:
            response = requests.get(
                'https://www.baidu.com',
                proxies={'http': proxy, 'https': proxy},
                timeout=5
            )
            self.update_score(proxy, response.status_code == 200)
        except:
            self.update_score(proxy, False)
            
    def _fetch_new_proxies(self):
        """从代理服务商获取新代理"""
        # 这里实现从代理服务商获取代理的逻辑
        # 示例：从免费代理网站爬取
        try:
            response = requests.get('https://www.kuaidaili.com/free/')
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                for tr in soup.find_all('tr'):
                    try:
                        ip = tr.find('td', {'data-title': 'IP'}).text
                        port = tr.find('td', {'data-title': 'PORT'}).text
                        proxy = f"http://{ip}:{port}"
                        self.add_proxy(proxy)
                    except:
                        continue
        except Exception as e:
            logger.error(f"获取新代理失败: {str(e)}")

class CookiePool:
    """Cookie池管理"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
        self.cookie_key = "cookie_pool"
        self.cookie_counter_key = "cookie_counter"
        self.max_uses = 1000  # 每个Cookie最大使用次数
        
    def add_cookie(self, domain: str, cookie: str):
        """添加Cookie"""
        key = f"{self.cookie_key}:{domain}"
        self.redis_client.sadd(key, cookie)
        self.redis_client.hset(self.cookie_counter_key, cookie, 0)
        
    def get_cookie(self, domain: str) -> Optional[str]:
        """获取Cookie"""
        key = f"{self.cookie_key}:{domain}"
        cookies = self.redis_client.smembers(key)
        if not cookies:
            return None
            
        # 选择使用次数最少的Cookie
        cookie_counts = [(cookie, int(self.redis_client.hget(self.cookie_counter_key, cookie) or 0))
                        for cookie in cookies]
        cookie_counts.sort(key=lambda x: x[1])
        
        if cookie_counts:
            cookie = cookie_counts[0][0]
            self.redis_client.hincrby(self.cookie_counter_key, cookie, 1)
            
            # 检查使用次数是否超限
            if int(self.redis_client.hget(self.cookie_counter_key, cookie)) >= self.max_uses:
                self.remove_cookie(domain, cookie)
                
            return cookie
            
        return None
        
    def remove_cookie(self, domain: str, cookie: str):
        """移除Cookie"""
        key = f"{self.cookie_key}:{domain}"
        self.redis_client.srem(key, cookie)
        self.redis_client.hdel(self.cookie_counter_key, cookie)
        
    def refresh_cookies(self, domain: str):
        """刷新指定域名的Cookies"""
        # 这里实现刷新Cookie的逻辑
        # 可以通过模拟登录等方式获取新Cookie
        pass

class RateLimiter:
    """请求频率限制器"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
        self.window_size = 60  # 时间窗口大小（秒）
        self.max_requests = {
            'default': 100,     # 默认限制
            'api.twitter.com': 300,  # Twitter API限制
            'xueqiu.com': 50,       # 雪球限制
            'eastmoney.com': 100,    # 东方财富限制
        }
        
    async def acquire(self, domain: str) -> bool:
        """获取请求许可"""
        current_time = int(time.time())
        window_key = f"rate_limit:{domain}:{current_time // self.window_size}"
        
        # 获取当前时间窗口的请求数
        count = int(self.redis_client.get(window_key) or 0)
        max_requests = self.max_requests.get(domain, self.max_requests['default'])
        
        if count >= max_requests:
            return False
            
        # 原子性递增并设置过期时间
        pipe = self.redis_client.pipeline()
        pipe.incr(window_key)
        pipe.expire(window_key, self.window_size)
        pipe.execute()
        
        return True
        
    async def wait_if_needed(self, domain: str):
        """如果需要，等待直到可以发送请求"""
        while not await self.acquire(domain):
            await asyncio.sleep(1)

class AntiCrawler:
    """反爬虫工具集成类"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.proxy_pool = ProxyPool(redis_url)
        self.cookie_pool = CookiePool(redis_url)
        self.rate_limiter = RateLimiter(redis_url)
        self.user_agent = UserAgent()
        
    async def get_session(self, domain: str) -> aiohttp.ClientSession:
        """获取配置好的会话"""
        # 等待频率限制
        await self.rate_limiter.wait_if_needed(domain)
        
        # 获取代理
        proxy = self.proxy_pool.get_proxy()
        
        # 获取Cookie
        cookie = self.cookie_pool.get_cookie(domain)
        
        # 构建请求头
        headers = {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        if cookie:
            headers['Cookie'] = cookie
            
        # 创建会话
        session = aiohttp.ClientSession(headers=headers)
        if proxy:
            session._proxy = proxy
            
        return session
        
    async def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[Union[Dict, str]]:
        """发送请求"""
        domain = url.split('/')[2]
        session = await self.get_session(domain)
        
        try:
            async with session:
                async with session.request(method, url, **kwargs) as response:
                    if response.status == 200:
                        # 更新代理分数
                        if hasattr(session, '_proxy'):
                            self.proxy_pool.update_score(session._proxy, True)
                            
                        # 根据响应类型返回数据
                        content_type = response.headers.get('Content-Type', '')
                        if 'application/json' in content_type:
                            return await response.json()
                        else:
                            return await response.text()
                    else:
                        # 更新代理分数
                        if hasattr(session, '_proxy'):
                            self.proxy_pool.update_score(session._proxy, False)
                        return None
                        
        except Exception as e:
            logger.error(f"请求失败: {str(e)}")
            # 更新代理分数
            if hasattr(session, '_proxy'):
                self.proxy_pool.update_score(session._proxy, False)
            return None
            
    def close(self):
        """关闭资源"""
        # 可以添加清理代码
        pass 