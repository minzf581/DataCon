from abc import ABC, abstractmethod
from typing import List, Dict, Any
import requests
import json
import pandas as pd
from dc_core.models import Dataset, DataRequirement, Project

class DataCollectorBase(ABC):
    """数据收集器基类"""
    
    @abstractmethod
    def collect(self, requirement: DataRequirement) -> Dataset:
        """收集数据"""
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """验证数据"""
        pass
    
    @abstractmethod
    def transform(self, data: Any) -> Dict:
        """转换数据"""
        pass

class WebAPICollector(DataCollectorBase):
    """Web API数据收集器"""
    
    def collect(self, requirement: DataRequirement) -> Dataset:
        """从Web API收集数据"""
        try:
            # 解析需求中的API配置
            api_config = self._parse_api_config(requirement.description)
            
            # 发送API请求
            response = requests.get(
                api_config['url'],
                headers=api_config.get('headers', {}),
                params=api_config.get('params', {}),
                timeout=30
            )
            response.raise_for_status()
            
            # 解析响应数据
            data = response.json()
            
            # 验证数据
            if not self.validate(data):
                raise ValueError("数据验证失败")
            
            # 转换数据
            transformed_data = self.transform(data)
            
            # 创建数据集
            dataset = Dataset.objects.create(
                name=f"API数据集_{requirement.id}",
                description=f"从{api_config['url']}收集的数据",
                project=requirement.project,
                format='json',
                size=len(str(transformed_data))
            )
            
            # 保存数据文件
            self._save_data_file(dataset, transformed_data)
            
            return dataset
            
        except Exception as e:
            raise Exception(f"数据收集失败: {str(e)}")
    
    def validate(self, data: Any) -> bool:
        """验证API返回的数据"""
        if not data:
            return False
            
        # 检查数据结构
        if not isinstance(data, (dict, list)):
            return False
            
        # 检查数据大小
        if len(str(data)) < 100:  # 数据太小可能无效
            return False
            
        return True
    
    def transform(self, data: Any) -> Dict:
        """转换API数据为标准格式"""
        try:
            # 将数据转换为DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                else:
                    df = pd.DataFrame([data])
            
            # 数据清洗
            df = self._clean_data(df)
            
            # 转换为字典格式
            return {
                'data': df.to_dict('records'),
                'metadata': {
                    'columns': list(df.columns),
                    'rows': len(df),
                    'dtypes': df.dtypes.to_dict()
                }
            }
        except Exception as e:
            raise Exception(f"数据转换失败: {str(e)}")
    
    def _parse_api_config(self, description: str) -> Dict:
        """从需求描述中解析API配置"""
        try:
            # 这里应该实现更复杂的解析逻辑
            # 当前简单实现
            config = json.loads(description)
            required_fields = ['url']
            if not all(field in config for field in required_fields):
                raise ValueError("API配置缺少必要字段")
            return config
        except json.JSONDecodeError:
            raise ValueError("无效的API配置格式")
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗数据"""
        # 删除重复行
        df = df.drop_duplicates()
        
        # 处理缺失值
        df = df.fillna({
            col: df[col].mode()[0] if df[col].dtype == 'object' else df[col].mean()
            for col in df.columns
        })
        
        # 删除全为空的列
        df = df.dropna(axis=1, how='all')
        
        return df
    
    def _save_data_file(self, dataset: Dataset, data: Dict) -> None:
        """保存数据文件"""
        # 这里应该实现文件存储逻辑
        # 可以使用Django的FileField或者外部存储服务
        pass

class DatabaseCollector(DataCollectorBase):
    """数据库数据收集器"""
    
    def collect(self, requirement: DataRequirement) -> Dataset:
        # 实现数据库数据收集逻辑
        pass
    
    def validate(self, data: Any) -> bool:
        # 实现数据库数据验证逻辑
        pass
    
    def transform(self, data: Any) -> Dict:
        # 实现数据库数据转换逻辑
        pass

class FileSystemCollector(DataCollectorBase):
    """文件系统数据收集器"""
    
    def collect(self, requirement: DataRequirement) -> Dataset:
        # 实现文件系统数据收集逻辑
        pass
    
    def validate(self, data: Any) -> bool:
        # 实现文件系统数据验证逻辑
        pass
    
    def transform(self, data: Any) -> Dict:
        # 实现文件系统数据转换逻辑
        pass

class DataCollectionService:
    """数据收集服务"""
    
    def __init__(self):
        self.collectors = {
            'web_api': WebAPICollector(),
            'database': DatabaseCollector(),
            'file_system': FileSystemCollector()
        }
    
    def collect_data(self, requirement: DataRequirement) -> Dataset:
        """根据需求收集数据"""
        # 根据需求选择合适的收集器
        collector = self._select_collector(requirement)
        
        # 更新需求状态
        requirement.status = 'collecting'
        requirement.save()
        
        try:
            # 收集数据
            dataset = collector.collect(requirement)
            requirement.status = 'completed'
            requirement.save()
            return dataset
        except Exception as e:
            requirement.status = 'failed'
            requirement.save()
            raise e
    
    def _select_collector(self, requirement: DataRequirement) -> DataCollectorBase:
        """选择合适的数据收集器"""
        try:
            # 解析需求配置
            config = json.loads(requirement.description)
            collector_type = config.get('type', 'web_api')
            
            if collector_type not in self.collectors:
                raise ValueError(f"不支持的收集器类型: {collector_type}")
                
            return self.collectors[collector_type]
        except json.JSONDecodeError:
            raise ValueError("无效的需求配置格式") 