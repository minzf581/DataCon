import requests
import json
from typing import Dict, Any

class AIDataPlatformClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.auth_token = self._get_auth_token(username, password)
        self.headers = {
            'Authorization': f'Token {self.auth_token}',
            'Content-Type': 'application/json'
        }
        
    def _get_auth_token(self, username: str, password: str) -> str:
        response = requests.post(f'{self.base_url}/auth/token/', json={
            'username': username,
            'password': password
        })
        return response.json()['token']
        
    def create_project(self, name: str, description: str) -> Dict[str, Any]:
        response = requests.post(
            f'{self.base_url}/projects/',
            headers=self.headers,
            json={
                'name': name,
                'description': description
            }
        )
        return response.json()
        
    def analyze_requirements(self, project_id: int, task_description: str,
                           agent_performance: Dict[str, float]) -> Dict[str, Any]:
        response = requests.post(
            f'{self.base_url}/datasets/analyze_requirements/',
            headers=self.headers,
            json={
                'project_id': project_id,
                'task_description': task_description,
                'agent_performance': agent_performance
            }
        )
        return response.json()
        
    def collect_data(self, project_id: int, requirements: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            f'{self.base_url}/datasets/collect_data/',
            headers=self.headers,
            json={
                'project_id': project_id,
                'requirements': requirements
            }
        )
        return response.json()
        
    def optimize_dataset(self, dataset_id: int, agent_performance: Dict[str, float]) -> Dict[str, Any]:
        response = requests.post(
            f'{self.base_url}/datasets/{dataset_id}/optimize/',
            headers=self.headers,
            json={'agent_performance': agent_performance}
        )
        return response.json()

def main():
    # 初始化客户端
    client = AIDataPlatformClient(
        base_url='http://localhost:8000/api',
        username='admin',
        password='admin'
    )
    
    # 创建项目
    project = client.create_project(
        name='图像分类项目',
        description='猫狗识别模型优化'
    )
    
    # 分析需求
    requirements = client.analyze_requirements(
        project_id=project['id'],
        task_description="需要一个图像分类模型来识别猫和狗，要求准确率达到95%以上",
        agent_performance={
            'accuracy': 0.85,
            'precision': 0.83,
            'recall': 0.82,
            'f1': 0.83
        }
    )
    
    # 采集数据
    dataset = client.collect_data(
        project_id=project['id'],
        requirements=requirements
    )
    
    # 优化数据集
    optimized_dataset = client.optimize_dataset(
        dataset_id=dataset['id'],
        agent_performance={
            'accuracy': 0.85,
            'precision': 0.83,
            'recall': 0.82,
            'f1': 0.83
        }
    )
    
    print("项目创建成功:", project)
    print("需求分析结果:", requirements)
    print("数据集采集结果:", dataset)
    print("数据集优化结果:", optimized_dataset)

if __name__ == '__main__':
    main() 