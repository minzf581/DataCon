from typing import Dict, List, Any
import pandas as pd
from datetime import datetime
import requests
from django.conf import settings
from django.utils import timezone
from dc_core.models import Dataset, DataRequirement
from dc_core.storage import DatasetStorage
from celery import shared_task
import uuid
import logging
from bs4 import BeautifulSoup
import sqlite3
import pymongo
import redis
from sqlalchemy import create_engine
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import time

logger = logging.getLogger(__name__)

class DataSourceConfig:
    """数据源配置"""
    
    def __init__(self, config=None, **kwargs):
        """初始化数据源配置
        
        Args:
            config: 配置字典
            **kwargs: 直接传入的配置参数
        """
        config = config or kwargs
        
        self.type = config.get('type') or config.get('source_type', 'api')
        self.url = config.get('url') or config.get('api_url')
        self.method = config.get('method', 'GET')
        self.headers = config.get('headers', {})
        self.params = config.get('params', {})
        self.auth = config.get('auth') or config.get('api_key')
        self.format = config.get('format', 'json')
        
        # 数据库配置
        self.db_config = config.get('db_config', {})
        
        # 爬虫配置
        self.crawler_config = config.get('crawler_config', {})
        
        # 流数据配置
        self.stream_config = config.get('stream_config', {})
        
        # 如果auth是API key，添加到headers中
        if self.auth and isinstance(self.auth, str):
            self.headers['Authorization'] = f'Bearer {self.auth}'
        
        # 如果没有提供auth，尝试从settings获取
        if not self.auth and hasattr(settings, 'API_KEY'):
            self.headers['Authorization'] = f'Bearer {settings.API_KEY}'

class EnhancedDataCollector:
    """增强型数据采集器"""
    
    def __init__(self):
        self.storage = DatasetStorage()
        self.max_workers = 5
        self.rate_limit = 100  # 每分钟请求数限制
        self._request_count = 0
        self._last_request_time = datetime.now()
        self.sensitive_fields = ['email', 'phone', 'password', 'ssn', 'credit_card']
    
    def create_collection_task(self, requirement, sync=False):
        """创建数据采集任务"""
        try:
            # 创建数据集记录
            dataset = Dataset.objects.create(
                name=f"Dataset-{uuid.uuid4().hex[:8]}",
                description=f"Data collection for: {requirement.get('description', 'N/A')}",
                status='pending',
                created_at=timezone.now()
            )
            
            if sync:
                # 同步执行
                collect_data(dataset.id, requirement)
                # 刷新数据集状态
                dataset.refresh_from_db()
            else:
                try:
                    # 异步执行
                    collect_data.delay(dataset.id, requirement)
                except Exception as e:
                    # 如果异步执行失败，尝试同步执行
                    collect_data(dataset.id, requirement)
                    # 刷新数据集状态
                    dataset.refresh_from_db()
            
            return dataset
            
        except Exception as e:
            raise ValueError(f"创建采集任务失败: {str(e)}")
    
    async def collect_from_api(self, config: DataSourceConfig) -> Dict:
        """从API采集数据"""
        try:
            # 检查速率限制
            self._check_rate_limit()
            
            session = aiohttp.ClientSession()
            try:
                if config.method == 'GET':
                    response = await session.get(
                        config.url,
                        headers=config.headers,
                        params=config.params,
                        timeout=30
                    )
                    await response.raise_for_status()
                    if config.format == 'json':
                        data = await response.json()
                        # 确保返回的数据格式正确
                        if isinstance(data, dict) and 'data' in data:
                            return data
                        elif isinstance(data, list):
                            return {'data': data}
                        else:
                            return {'data': [data] if data else []}
                    else:
                        content = await response.text()
                        if config.format == 'csv':
                            data = pd.read_csv(content).to_dict('records')
                            return {'data': data}
                        else:
                            raise ValueError(f"不支持的数据格式: {config.format}")
                else:
                    raise ValueError(f"不支持的请求方法: {config.method}")
            finally:
                await session.close()
            
        except Exception as e:
            logger.error(f"API数据采集失败: {str(e)}")
            raise ValueError(f"API数据采集失败: {str(e)}")
            
        return {'data': []}
    
    def collect_from_database(self, config: DataSourceConfig) -> List[Dict]:
        """从数据库采集数据"""
        try:
            db_type = config.db_config.get('type')
            if db_type == 'mysql':
                return self._collect_from_mysql(config)
            elif db_type == 'mongodb':
                return self._collect_from_mongodb(config)
            elif db_type == 'sqlite':
                return self._collect_from_sqlite(config)
            else:
                raise ValueError(f"不支持的数据库类型: {db_type}")
        except Exception as e:
            raise ValueError(f"数据库采集失败: {str(e)}")
    
    def collect_from_web(self, config: DataSourceConfig) -> List[Dict]:
        """从网页采集数据"""
        try:
            # 获取网页内容
            response = requests.get(
                config.url,
                headers=config.headers,
                timeout=30
            )
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 根据配置提取数据
            selector = config.crawler_config.get('selector')
            if selector:
                elements = soup.select(selector)
                data = []
                for element in elements:
                    item = {}
                    for field, field_selector in config.crawler_config.get('fields', {}).items():
                        field_element = element.select_one(field_selector)
                        item[field] = field_element.text.strip() if field_element else None
                    data.append(item)
                return data
            
            return []
            
        except Exception as e:
            raise ValueError(f"网页采集失败: {str(e)}")
    
    async def collect_stream_data(self, config: DataSourceConfig, callback) -> None:
        """采集流数据"""
        try:
            if config.stream_config.get('type') == 'websocket':
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(config.url) as ws:
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                await callback(data)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
            else:
                raise ValueError(f"不支持的流数据类型: {config.stream_config.get('type')}")
                
        except Exception as e:
            raise ValueError(f"流数据采集失败: {str(e)}")
    
    def _collect_from_mysql(self, config: DataSourceConfig) -> List[Dict]:
        """从MySQL数据库采集数据"""
        engine = create_engine(config.db_config.get('connection_string'))
        query = config.db_config.get('query')
        return pd.read_sql(query, engine).to_dict('records')
    
    def _collect_from_mongodb(self, config: DataSourceConfig) -> List[Dict]:
        """从MongoDB数据库采集数据"""
        client = pymongo.MongoClient(config.db_config.get('connection_string'))
        db = client[config.db_config.get('database')]
        collection = db[config.db_config.get('collection')]
        return list(collection.find(config.db_config.get('query', {})))
    
    def _collect_from_sqlite(self, config: DataSourceConfig) -> List[Dict]:
        """从SQLite数据库采集数据"""
        try:
            # 如果在测试模式下，使用测试连接
            if hasattr(self, '_test_conn'):
                conn = self._test_conn
            else:
                conn = sqlite3.connect(config.db_config.get('database_path'))
            
            try:
                query = config.db_config.get('query')
                data = pd.read_sql(query, conn).to_dict('records')
                return data
            finally:
                # 只有在非测试模式下才关闭连接
                if not hasattr(self, '_test_conn'):
                    conn.close()
        except Exception as e:
            raise e
    
    def _check_rate_limit(self) -> None:
        """检查并控制请求速率"""
        current_time = datetime.now()
        time_diff = (current_time - self._last_request_time).total_seconds()
        
        if time_diff >= 60:  # 重置计数器
            self._request_count = 0
            self._last_request_time = current_time
        
        if self._request_count >= self.rate_limit:
            sleep_time = 60 - time_diff
            if sleep_time > 0:
                time.sleep(sleep_time)
                self._request_count = 0
                self._last_request_time = datetime.now()
        
        self._request_count += 1
    
    def clean_data(self, raw_data: List[Dict], fields: List[str]) -> List[Dict]:
        """清洗数据"""
        try:
            # 转换为DataFrame进行处理
            df = pd.DataFrame(raw_data)
            
            # 只保留指定字段
            if fields:
                df = df[fields]
            
            # 删除重复行
            df = df.drop_duplicates()
            
            # 处理缺失值
            df = df.fillna(df.mean(numeric_only=True))
            
            # 转换回字典列表
            return df.to_dict('records')
            
        except Exception as e:
            raise ValueError(f"数据清洗失败: {str(e)}")
    
    def validate_data_privacy(self, data: List[Dict]) -> bool:
        """验证数据隐私合规性"""
        try:
            # 检查是否包含敏感字段
            for item in data:
                for field in item.keys():
                    if field.lower() in self.sensitive_fields:
                        return False
            return True
            
        except Exception as e:
            raise ValueError(f"隐私验证失败: {str(e)}")

@shared_task
def collect_data(dataset_id, requirement):
    """执行数据采集"""
    dataset = None
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        dataset.status = 'processing'
        dataset.save()
        
        # 配置数据源
        config = DataSourceConfig(requirement)
        collector = EnhancedDataCollector()
        
        # 根据数据源类型选择采集方法
        if config.type == 'api':
            # 使用异步IO采集API数据
            loop = asyncio.get_event_loop()
            data = loop.run_until_complete(collector.collect_from_api(config))
        elif config.type == 'database':
            data = collector.collect_from_database(config)
        elif config.type == 'web':
            data = collector.collect_from_web(config)
        else:
            raise ValueError(f"不支持的数据源类型: {config.type}")
        
        # 解析数据
        if isinstance(data, dict) and 'data' in data:
            data = data['data']
        if not isinstance(data, list):
            data = [data]
        
        # 更新数据集
        dataset.status = 'completed'
        dataset.size = len(data)
        dataset.save()
        
        # 保存数据
        collector.storage.save_dataset(dataset, {
            'data': data,
            'metadata': {
                'source_type': config.type,
                'source_url': config.url,
                'collected_at': datetime.now().isoformat()
            }
        })
        
        return True
    except Exception as e:
        if dataset:
            dataset.status = 'failed'
            dataset.error_message = str(e)
            dataset.save()
        logger.error(f"数据采集失败: {str(e)}")
        raise e 