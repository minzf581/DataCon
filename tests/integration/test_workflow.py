import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

User = get_user_model()

@pytest.mark.integration
class WorkflowTests(TestCase):
    def setUp(self):
        """测试前准备工作"""
        super().setUp()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client = APIClient()
        
        # 创建认证令牌
        self.token = Token.objects.create(user=self.user)

    def test_complete_workflow(self):
        """测试完整工作流程"""
        # 测试未认证访问
        self.client.logout()  # 确保未认证状态
        response = self.client.get('/api/v1/')
        self.assertEqual(response.status_code, 401)
        
        # 测试使用令牌认证
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get('/api/v1/')
        self.assertEqual(response.status_code, 200)
        
        # 测试受限资源访问
        response = self.client.post('/api/v1/restricted/')
        self.assertEqual(response.status_code, 401)
        
        # 测试注销
        self.client.credentials()  # 清除认证信息
        response = self.client.get('/api/v1/')
        self.assertEqual(response.status_code, 401)
        
        # 使用错误的认证信息访问
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid-token')
        response = self.client.get('/api/v1/')
        self.assertEqual(response.status_code, 401) 