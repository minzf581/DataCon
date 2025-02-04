import os
import json
import shutil
from typing import Dict, Any
from django.conf import settings
from dc_core.models import Dataset

class DatasetStorage:
    """数据集存储管理器"""
    
    def __init__(self):
        self.storage_path = settings.DATASET_STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)
    
    def save_dataset(self, dataset: Dataset, content: Dict[str, Any]) -> str:
        """保存数据集内容"""
        # 创建数据集目录
        dataset_dir = self._get_dataset_dir(dataset)
        os.makedirs(dataset_dir, exist_ok=True)
        
        # 保存数据文件
        file_path = os.path.join(dataset_dir, 'data.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    def load_dataset(self, dataset: Dataset) -> Dict[str, Any]:
        """加载数据集内容"""
        file_path = os.path.join(self._get_dataset_dir(dataset), 'data.json')
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"数据集文件不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def delete_dataset(self, dataset: Dataset) -> None:
        """删除数据集文件"""
        dataset_dir = self._get_dataset_dir(dataset)
        if os.path.exists(dataset_dir):
            shutil.rmtree(dataset_dir)
    
    def _get_dataset_dir(self, dataset: Dataset) -> str:
        """获取数据集目录路径"""
        return os.path.join(self.storage_path, str(dataset.id)) 