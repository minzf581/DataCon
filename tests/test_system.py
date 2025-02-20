import unittest
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from dc_core.models import Dataset, Project
from dc_validation.services import DataQualityService
from dc_core.services.data_processing import DataProcessor
import json
import pandas as pd
import numpy as np

User = get_user_model()

@pytest.mark.django_db
class SystemTest(TestCase):
    """系统集成测试"""
    
    def setUp(self):
        """测试准备工作"""
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # 创建测试客户端
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # 创建测试项目
        self.project = Project.objects.create(
            name='测试项目',
            description='用于系统测试的项目',
            objective='测试系统功能',
            owner=self.user
        )
        
        # 创建测试数据集
        self.dataset = Dataset.objects.create(
            name='测试数据集',
            description='用于测试的数据集',
            project=self.project,
            format='csv',
            size=1000
        )
        
        # 初始化服务
        self.quality_service = DataQualityService()
        self.data_processor = DataProcessor(self.dataset)
    
    def test_financial_api_endpoints(self):
        """测试金融数据 API 端点"""
        print("\n测试金融数据 API 端点...")
        
        # 测试市场数据端点
        response = self.client.get('/api/financial/market_data/', {
            'symbol': 'AAPL',
            'interval': '1d'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("市场数据 API 测试通过")
        
        # 测试技术指标端点
        response = self.client.get('/api/financial/technical_indicators/', {
            'symbol': 'AAPL',
            'indicator': 'RSI',
            'period': 14
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("技术指标 API 测试通过")
        
        # 测试基本面数据端点
        response = self.client.get('/api/financial/fundamental_data/', {
            'symbol': 'AAPL',
            'data_type': 'financials'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("基本面数据 API 测试通过")
    
    def test_data_processing(self):
        """测试数据处理功能"""
        print("\n测试数据处理功能...")
        
        # 创建测试数据
        test_data = pd.DataFrame({
            'A': np.random.randn(100),
            'B': np.random.randn(100),
            'C': np.random.choice(['X', 'Y', 'Z'], 100)
        })
        
        # 测试数据预览
        preview = self.data_processor.get_preview(rows=5)
        self.assertIsNotNone(preview)
        self.assertIn('columns', preview)
        self.assertIn('rows', preview)
        print("数据预览功能测试通过")
        
        # 测试数据统计
        stats = self.data_processor.get_statistics()
        self.assertIsNotNone(stats)
        print("数据统计功能测试通过")
        
        # 测试数据清洗
        cleaned_data = self.data_processor.clean_data()
        self.assertIsNotNone(cleaned_data)
        print("数据清洗功能测试通过")
    
    def test_data_validation(self):
        """测试数据验证功能"""
        print("\n测试数据验证功能...")
        
        # 测试数据质量评分
        quality_score = self.quality_service.evaluate_dataset(self.dataset)
        self.assertIsInstance(quality_score, float)
        self.assertTrue(0 <= quality_score <= 100)
        print("数据质量评分功能测试通过")
        
        # 测试数据模式验证
        schema = {
            'A': 'float',
            'B': 'float',
            'C': 'str'
        }
        validation_result = self.quality_service.validate_schema(
            data=[{'A': 1.0, 'B': 2.0, 'C': 'X'}],
            expected_schema=schema
        )
        self.assertTrue(validation_result['is_valid'])
        print("数据模式验证功能测试通过")
    
    def test_error_handling(self):
        """测试错误处理"""
        print("\n测试错误处理...")
        
        # 测试无效请求处理
        response = self.client.get('/api/financial/market_data/', {
            'symbol': 'INVALID_SYMBOL'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print("无效请求处理测试通过")
        
        # 测试未认证访问
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/financial/market_data/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # Django REST framework 使用 401 表示未认证
        print("未认证访问处理测试通过")
    
    def test_performance(self):
        """测试性能"""
        print("\n测试性能...")
        
        import time
        
        # 测试 API 响应时间
        start_time = time.time()
        response = self.client.get('/api/financial/market_data/', {
            'symbol': 'AAPL',
            'interval': '1d'
        })
        end_time = time.time()
        
        response_time = end_time - start_time
        self.assertLess(response_time, 5.0)  # 响应时间应小于5秒
        print(f"API 响应时间: {response_time:.2f}秒")
        
        # 测试数据处理性能
        start_time = time.time()
        self.data_processor.get_statistics()
        end_time = time.time()
        
        processing_time = end_time - start_time
        self.assertLess(processing_time, 3.0)  # 处理时间应小于3秒
        print(f"数据处理时间: {processing_time:.2f}秒")
    
    @pytest.mark.skip(reason="OpenBB integration not configured")
    def test_openbb_integration(self):
        """测试OpenBB集成"""
        print("\n测试OpenBB集成...")
        
        # 测试市场数据
        response = self.client.get('/api/financial/market_data/', {
            'symbol': 'AAPL',
            'source': 'openbb'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('market_data', response.data)
        print("OpenBB市场数据测试通过")
        
        # 测试基本面数据
        response = self.client.get('/api/financial/fundamental_data/', {
            'symbol': 'AAPL',
            'source': 'openbb'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('fundamentals', response.data)
        print("OpenBB基本面数据测试通过")
        
        # 测试技术指标
        response = self.client.get('/api/financial/technical_indicators/', {
            'symbol': 'AAPL',
            'source': 'openbb'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('technicals', response.data)
        print("OpenBB技术指标测试通过")
    
    def tearDown(self):
        """清理测试数据"""
        self.user.delete()
        self.project.delete()
        self.dataset.delete()

if __name__ == '__main__':
    unittest.main() 