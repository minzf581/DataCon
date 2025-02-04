from typing import Dict, List, Optional
import requests
from django.conf import settings
from dc_core.models import Dataset, Project, AgentPerformance
from dc_validation.services import DataQualityService
from dc_analysis.services import DataAnalysisService
from dc_core.storage import DatasetStorage
import json

class AITrainingIntegrationService:
    """AI训练平台集成服务"""
    
    def __init__(self):
        self.data_quality_service = DataQualityService()
        self.data_analysis_service = DataAnalysisService()
        self.api_base_url = settings.AI_TRAINING_PLATFORM_URL
        self.api_key = settings.AI_TRAINING_PLATFORM_API_KEY
    
    def submit_dataset(self, dataset: Dataset) -> Dict:
        """提交数据集到AI训练平台"""
        try:
            # 评估数据集质量
            quality_score = self.data_quality_service.evaluate_dataset(dataset)
            
            if quality_score < settings.MIN_DATASET_QUALITY_SCORE:
                raise ValueError(f"数据集质量分数({quality_score})低于最小要求({settings.MIN_DATASET_QUALITY_SCORE})")
            
            # 准备数据集元数据
            metadata = self._prepare_dataset_metadata(dataset)
            
            # 上传数据集到训练平台
            response = self._upload_dataset(dataset, metadata)
            
            # 记录提交结果
            self._record_submission(dataset, response)
            
            return response
            
        except Exception as e:
            # 记录错误
            self._record_error(dataset, str(e))
            raise
    
    def get_training_status(self, dataset: Dataset) -> Dict:
        """获取训练状态"""
        try:
            response = requests.get(
                f"{self.api_base_url}/training/status/{dataset.external_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            status_data = response.json()
            self._update_performance_metrics(dataset, status_data)
            
            return status_data
            
        except Exception as e:
            self._record_error(dataset, f"获取训练状态失败: {str(e)}")
            raise
    
    def get_model_metrics(self, dataset: Dataset) -> Dict:
        """获取模型指标"""
        try:
            response = requests.get(
                f"{self.api_base_url}/model/metrics/{dataset.external_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            metrics_data = response.json()
            self._update_performance_metrics(dataset, metrics_data)
            
            return metrics_data
            
        except Exception as e:
            self._record_error(dataset, f"获取模型指标失败: {str(e)}")
            raise
    
    def _prepare_dataset_metadata(self, dataset: Dataset) -> Dict:
        """准备数据集元数据"""
        return {
            'dataset_id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'format': dataset.format,
            'size': dataset.size,
            'quality_score': dataset.quality_score,
            'created_at': dataset.created_at.isoformat(),
            'project': {
                'id': dataset.project.id,
                'name': dataset.project.name,
                'objective': dataset.project.objective
            }
        }
    
    def _upload_dataset(self, dataset: Dataset, metadata: Dict) -> Dict:
        """上传数据集到训练平台"""
        # 准备上传数据
        files = {
            'metadata': ('metadata.json', json.dumps(metadata)),
            'dataset': ('dataset.json', self._get_dataset_content(dataset))
        }
        
        # 发送上传请求
        response = requests.post(
            f"{self.api_base_url}/datasets/upload",
            headers=self._get_headers(),
            files=files
        )
        response.raise_for_status()
        
        return response.json()
    
    def _get_dataset_content(self, dataset: Dataset) -> str:
        """获取数据集内容"""
        storage = DatasetStorage()
        try:
            content = storage.load_dataset(dataset)
            return json.dumps(content, ensure_ascii=False)
        except FileNotFoundError:
            raise ValueError(f"数据集{dataset.id}的文件不存在")
    
    def _get_headers(self) -> Dict:
        """获取API请求头"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def _record_submission(self, dataset: Dataset, response: Dict) -> None:
        """记录数据集提交结果"""
        dataset.external_id = response.get('dataset_id')
        dataset.status = 'submitted'
        dataset.save()
    
    def _record_error(self, dataset: Dataset, error_message: str) -> None:
        """记录错误信息"""
        dataset.status = 'error'
        dataset.error_message = error_message
        dataset.save()
    
    def _update_performance_metrics(self, dataset: Dataset, metrics_data: Dict) -> None:
        """更新性能指标"""
        if not metrics_data.get('metrics'):
            return
            
        AgentPerformance.objects.create(
            dataset=dataset,
            project=dataset.project,
            metrics=metrics_data['metrics']
        ) 