import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
from datetime import datetime
from django.test import TestCase
from dc_core.services.requirement_analysis import RequirementAnalysisService
from dc_collector.services.enhanced_collector import EnhancedDataCollector as EnhancedCollector, DataSourceConfig
from dc_core.models import Dataset
from dc_core.storage import DatasetStorage
from dc_core.services.quality_manager import DataQualityManager
from dc_core.services.ai_enhancer import AIEnhancer
import aiohttp
import sqlite3
import pytest
import pandas as pd

class RequirementAnalysisTests(TestCase):
    """需求分析服务测试"""
    
    def setUp(self):
        self.service = RequirementAnalysisService()
        
    def test_analyze_requirement(self):
        """测试需求分析"""
        # 模拟OpenAI响应
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "data_type": "cryptocurrency",
                        "timeframe": "last_week",
                        "fields": ["price", "volume"],
                        "frequency": "daily",
                        "format": "json",
                        "source_type": "api"
                    })
                )
            )
        ]
        
        # 使用mock替换OpenAI客户端的方法
        self.service.openai_client.chat.completions.create = MagicMock(return_value=mock_response)
        
        # 测试需求分析
        result = self.service.analyze_requirement(
            "I need Bitcoin price and volume data for the last week"
        )
        
        # 验证结果
        self.assertEqual(result["data_type"], "cryptocurrency")
        self.assertEqual(result["timeframe"], "last_week")
        self.assertListEqual(result["fields"], ["price", "volume"])
        
    def test_validate_requirement(self):
        """测试需求验证"""
        # 有效需求
        valid_req = {
            "data_type": "cryptocurrency",
            "timeframe": "last_week",
            "fields": ["price", "volume"]
        }
        self.assertTrue(self.service.validate_requirement(valid_req))
        
        # 无效需求
        invalid_req = {
            "data_type": "cryptocurrency",
            "fields": ["price"]  # 缺少timeframe
        }
        self.assertFalse(self.service.validate_requirement(invalid_req))

class EnhancedDataCollectorTests(TestCase):
    """增强型数据采集器测试"""
    
    def setUp(self):
        self.collector = EnhancedCollector()
        
    @pytest.mark.asyncio
    async def test_collect_from_api(self):
        """测试API数据采集"""
        config = DataSourceConfig({
            'type': 'api',
            'url': 'https://api.example.com/data',
            'method': 'GET',
            'headers': {'Content-Type': 'application/json'},
            'auth': 'test-api-key',
            'format': 'json'
        })
        
        # 创建mock响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'data': [
                {'id': 1, 'value': 'test1'},
                {'id': 2, 'value': 'test2'}
            ]
        })
        mock_response.raise_for_status = AsyncMock()
        
        # 创建mock会话
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.close = AsyncMock()
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            data = await self.collector.collect_from_api(config)
            self.assertEqual(len(data['data']), 2)
            self.assertEqual(data['data'][0]['value'], 'test1')
        
    def test_clean_data(self):
        """测试数据清洗"""
        # 测试数据
        raw_data = [
            {"price": 50000, "volume": 1000, "extra": "value1"},
            {"price": 50000, "volume": 1000, "extra": "value2"},  # 重复行
            {"price": None, "volume": 1200, "extra": "value3"}
        ]
        
        # 指定字段
        fields = ["price", "volume"]
        
        # 清洗数据
        cleaned_data = self.collector.clean_data(raw_data, fields)
        
        # 验证结果
        self.assertEqual(len(cleaned_data), 2)  # 应该删除重复行
        self.assertNotIn("extra", cleaned_data[0])  # 应该只包含指定字段
        self.assertIsNotNone(cleaned_data[1]["price"])  # 应该处理缺失值
        
    def test_validate_data_privacy(self):
        """测试隐私合规性验证"""
        # 安全数据
        safe_data = [
            {"price": 50000, "volume": 1000},
            {"timestamp": "2024-01-01", "value": 100}
        ]
        self.assertTrue(self.collector.validate_data_privacy(safe_data))
        
        # 包含敏感信息的数据
        unsafe_data = [
            {"price": 50000, "email": "user@example.com"},
            {"phone": "1234567890", "value": 100}
        ]
        self.assertFalse(self.collector.validate_data_privacy(unsafe_data))

class DatasetStorageTests(TestCase):
    """数据集存储测试"""
    
    def setUp(self):
        self.storage = DatasetStorage()
        self.dataset = Dataset.objects.create(
            name="test_dataset",
            description="Test dataset",
            format="json"
        )
        
    def test_save_and_load_dataset(self):
        """测试数据集保存和加载"""
        # 测试数据
        test_data = {
            "data": [
                {"price": 50000, "volume": 1000},
                {"price": 51000, "volume": 1200}
            ],
            "metadata": {
                "source": "test",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # 保存数据集
        file_path = self.storage.save_dataset(self.dataset, test_data)
        self.assertTrue(file_path.endswith('data.json'))
        
        # 加载数据集
        loaded_data = self.storage.load_dataset(self.dataset)
        self.assertEqual(len(loaded_data["data"]), 2)
        self.assertEqual(loaded_data["data"][0]["price"], 50000)
        
    def test_delete_dataset(self):
        """测试数据集删除"""
        # 先保存数据
        test_data = {"data": [], "metadata": {}}
        self.storage.save_dataset(self.dataset, test_data)
        
        # 删除数据集
        self.storage.delete_dataset(self.dataset)
        
        # 验证文件已删除
        with self.assertRaises(FileNotFoundError):
            self.storage.load_dataset(self.dataset)

class IntegrationTests(TestCase):
    """集成测试"""
    
    def setUp(self):
        self.requirement_service = RequirementAnalysisService()
        self.collector = EnhancedCollector()
        
        # 创建OpenAI mock响应
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps({
                        "data_type": "cryptocurrency",
                        "timeframe": "last_week",
                        "fields": ["price", "volume"]
                    })
                )
            )
        ]
        self.requirement_service.openai_client.chat.completions.create = MagicMock(return_value=mock_response)
    
    def test_end_to_end_flow(self):
        """测试完整流程"""
        # 1. 测试需求分析
        requirement_text = "I need Bitcoin price and volume data for the last week"
        requirement = self.requirement_service.analyze_requirement(requirement_text)
        
        # 2. 验证需求分析结果
        self.assertEqual(requirement["data_type"], "cryptocurrency")
        self.assertEqual(requirement["timeframe"], "last_week")
        self.assertListEqual(requirement["fields"], ["price", "volume"])
        
        # 3. 添加数据源信息
        requirement.update({
            'type': 'api',
            'url': 'https://api.example.com/crypto',
            'method': 'GET',
            'format': 'json',
            'auth': 'test-api-key'
        })
        
        # 4. 模拟API响应
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "data": [
                {"price": 50000, "volume": 1000},
                {"price": 51000, "volume": 1200}
            ]
        })
        mock_response.raise_for_status = AsyncMock()
        
        # 创建mock会话
        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.close = AsyncMock()
        
        with patch('aiohttp.ClientSession', return_value=mock_session):
            # 5. 创建数据集
            dataset = self.collector.create_collection_task(requirement, sync=True)
            
            # 6. 验证结果
            self.assertEqual(dataset.status, 'completed')
            self.assertEqual(dataset.size, 2)

class DataQualityTests(TestCase):
    """数据质量测试"""
    
    def setUp(self):
        self.quality_manager = DataQualityManager()
        
    def test_schema_validation(self):
        """测试数据模式验证"""
        # 测试数据
        data = [
            {"id": 1, "name": "test1", "value": 100},
            {"id": 2, "name": "test2", "value": 200}
        ]
        
        # 正确的模式
        valid_schema = {
            "id": "int",
            "name": "str",
            "value": "int"
        }
        
        # 验证结果
        result = self.quality_manager.validate_schema(data, valid_schema)
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['missing_fields']), 0)
        
        # 错误的模式
        invalid_schema = {
            "id": "str",
            "name": "int",
            "missing_field": "str"
        }
        
        result = self.quality_manager.validate_schema(data, invalid_schema)
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['type_mismatches']), 0)
        self.assertIn('missing_field', result['missing_fields'])
    
    def test_quality_score(self):
        """测试质量评分"""
        # 创建测试数据集
        dataset = Dataset.objects.create(
            name="test_dataset",
            description="Test Dataset",
            status="completed"
        )
        
        # 计算质量分数
        score = self.quality_manager.calculate_quality_score(dataset)
        
        # 验证结果
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

class AIEnhancerTests(TestCase):
    """AI增强功能测试"""
    
    def setUp(self):
        self.mock_openai = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"analysis": {"data_type": "user_behavior", "complexity": "medium"}}'
                )
            )
        ]
        self.mock_openai.chat.completions.create.return_value = mock_response
        self.ai_enhancer = AIEnhancer(openai_client=self.mock_openai)
    
    def test_complex_requirement_analysis(self):
        requirement_text = "需要收集用户购买行为数据"
        result = self.ai_enhancer.analyze_complex_requirements(requirement_text)
        self.assertIsInstance(result, dict)
        self.assertIn('analysis', result)
        
    def test_data_source_suggestion(self):
        # 更新mock响应
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='[{"name": "用户行为数据库", "type": "database", "url": "example.com"}]'
                )
            )
        ]
        self.mock_openai.chat.completions.create.return_value = mock_response
        
        requirement = {
            'data_type': '用户行为',
            'fields': ['user_id', 'action', 'timestamp']
        }
        suggestions = self.ai_enhancer.suggest_data_sources(requirement)
        self.assertIsInstance(suggestions, list)
        self.assertTrue(len(suggestions) > 0)
    
    def test_anomaly_detection(self):
        """测试异常检测"""
        # 创建测试数据集
        dataset = Dataset.objects.create(
            name="test_dataset",
            description="Test Dataset",
            status="completed"
        )
        
        # 检测异常
        result = self.ai_enhancer.detect_anomalies(dataset)
        
        # 验证结果
        self.assertIn('anomaly_count', result)
        self.assertIn('anomaly_percentage', result)
        self.assertIn('anomaly_records', result)
    
    def test_feature_extraction(self):
        """测试特征提取"""
        # 创建测试数据集
        dataset = Dataset.objects.create(
            name="test_dataset",
            description="Test Dataset",
            status="completed"
        )
        
        # 提取特征
        features = self.ai_enhancer.extract_features(dataset)
        
        # 验证结果
        self.assertIn('basic_stats', features)
        self.assertIn('correlations', features)
        self.assertIn('distributions', features)

class EnhancedCollectorTests(TestCase):
    """增强型数据采集器测试"""
    
    def setUp(self):
        """测试前准备工作"""
        super().setUp()
        self.collector = EnhancedCollector()
        
        # 创建测试数据库
        self.db_path = ':memory:'
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # 创建测试表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value INTEGER NOT NULL
            )
        ''')
        
        # 插入测试数据
        self.cursor.executemany(
            'INSERT INTO test_table (name, value) VALUES (?, ?)',
            [('test1', 100), ('test2', 200)]
        )
        self.conn.commit()
        
        # 设置测试数据库连接
        self.collector._test_conn = self.conn
    
    def tearDown(self):
        """测试后清理工作"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.execute('DROP TABLE IF EXISTS test_table')
            self.conn.commit()
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        super().tearDown()
    
    def test_database_collection(self):
        """测试数据库数据采集"""
        # 配置数据源
        config = DataSourceConfig({
            'type': 'database',
            'db_config': {
                'type': 'sqlite',
                'database_path': self.db_path,
                'query': 'SELECT * FROM test_table'
            }
        })
        
        # 采集数据
        data = self.collector.collect_from_database(config)
        
        # 验证结果
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], 'test1')
        self.assertEqual(data[1]['value'], 200)
    
    @patch('requests.get')
    def test_web_collection(self, mock_get):
        """测试网页数据采集"""
        # 配置数据源
        config = DataSourceConfig({
            'type': 'web',
            'url': 'https://example.com',
            'crawler_config': {
                'selector': 'table tr',
                'fields': {
                    'name': 'td:nth-child(1)',
                    'value': 'td:nth-child(2)'
                }
            }
        })
        
        # 模拟响应
        mock_response = MagicMock()
        mock_response.text = """
        <table>
            <tr><td>name1</td><td>100</td></tr>
            <tr><td>name2</td><td>200</td></tr>
        </table>
        """
        mock_get.return_value = mock_response
        
        # 采集数据
        data = self.collector.collect_from_web(config)
        
        # 验证结果
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], 'name1')
        self.assertEqual(data[1]['value'], '200')
    
    @patch('aiohttp.ClientSession.ws_connect')
    async def test_stream_collection(self, mock_ws):
        """测试流数据采集"""
        # 配置数据源
        config = DataSourceConfig({
            'type': 'stream',
            'url': 'wss://example.com/stream',
            'stream_config': {
                'type': 'websocket'
            }
        })
        
        # 模拟WebSocket消息
        received_data = []
        async def callback(data):
            received_data.append(data)
        
        # 模拟WebSocket连接
        mock_ws_conn = MagicMock()
        mock_ws_conn.__aenter__.return_value = mock_ws_conn
        mock_ws_conn.__aiter__.return_value = [
            MagicMock(type=aiohttp.WSMsgType.TEXT, data='{"value": 100}'),
            MagicMock(type=aiohttp.WSMsgType.TEXT, data='{"value": 200}'),
            MagicMock(type=aiohttp.WSMsgType.ERROR)
        ]
        mock_ws.return_value = mock_ws_conn
        
        # 采集数据
        await self.collector.collect_stream_data(config, callback)
        
        # 验证结果
        self.assertEqual(len(received_data), 2)
        self.assertEqual(received_data[0]['value'], 100)
        self.assertEqual(received_data[1]['value'], 200) 