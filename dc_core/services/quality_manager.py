from typing import Dict, List, Any
import pandas as pd
import numpy as np
from dc_core.models import Dataset, DataQualityMetric
from django.utils import timezone
from scipy import stats

class DataQualityManager:
    """数据质量管理器"""
    
    def __init__(self):
        self.quality_thresholds = {
            'completeness': 0.8,  # 完整性阈值
            'consistency': 0.9,   # 一致性阈值
            'accuracy': 0.85      # 准确性阈值
        }
    
    def validate_schema(self, data: List[Dict], expected_schema: Dict) -> Dict:
        """验证数据模式"""
        try:
            df = pd.DataFrame(data)
            validation_results = {
                'missing_fields': [],
                'type_mismatches': [],
                'is_valid': True
            }
            
            # 检查必需字段
            for field, field_type in expected_schema.items():
                if field not in df.columns:
                    validation_results['missing_fields'].append(field)
                    validation_results['is_valid'] = False
                else:
                    # 检查数据类型
                    actual_type = df[field].dtype
                    if not self._check_type_compatibility(actual_type, field_type):
                        validation_results['type_mismatches'].append({
                            'field': field,
                            'expected': field_type,
                            'actual': str(actual_type)
                        })
                        validation_results['is_valid'] = False
            
            return validation_results
        except Exception as e:
            raise ValueError(f"模式验证失败: {str(e)}")
    
    def calculate_quality_score(self, dataset: Dataset) -> float:
        """计算数据质量评分"""
        try:
            # 加载数据集数据
            data = self._load_dataset_data(dataset)
            if not data:
                return 0.0
                
            # 转换为DataFrame
            df = pd.DataFrame(data)
            
            # 计算完整性分数
            non_null_ratio = 1 - df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
            completeness_score = float(non_null_ratio)
            
            # 计算一致性分数
            consistency_score = float(self._calculate_consistency_score(df))
            
            # 计算准确性分数
            accuracy_score = float(self._calculate_accuracy_score(df))
            
            # 计算总分
            total_score = (completeness_score + consistency_score + accuracy_score) / 3
            
            # 保存评分
            metrics = {
                'completeness_score': completeness_score,
                'consistency_score': consistency_score,
                'accuracy_score': accuracy_score,
                'total_score': total_score
            }
            self._save_quality_metrics(dataset, metrics)
            
            return total_score
            
        except Exception as e:
            raise ValueError(f"质量评分计算失败: {str(e)}")
            
    def _calculate_consistency_score(self, df: pd.DataFrame) -> float:
        """计算数据一致性分数"""
        try:
            # 检查数值列的标准差
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            if len(numeric_cols) > 0:
                std_scores = 1 - df[numeric_cols].std() / df[numeric_cols].mean()
                return float(std_scores.mean())
            return 1.0
        except:
            return 0.0
            
    def _calculate_accuracy_score(self, df: pd.DataFrame) -> float:
        """计算数据准确性分数"""
        try:
            # 检查数值是否在合理范围内
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            if len(numeric_cols) > 0:
                z_scores = np.abs(stats.zscore(df[numeric_cols]))
                accuracy_ratio = (z_scores < 3).mean()
                return float(accuracy_ratio)
            return 1.0
        except:
            return 0.0
    
    def _check_type_compatibility(self, actual_type: Any, expected_type: str) -> bool:
        """检查数据类型兼容性"""
        type_mappings = {
            'int': ['int64', 'int32'],
            'float': ['float64', 'float32'],
            'str': ['object'],
            'datetime': ['datetime64[ns]']
        }
        return str(actual_type) in type_mappings.get(expected_type, [])
    
    def _load_dataset_data(self, dataset: Dataset) -> List[Dict]:
        """加载数据集数据"""
        # 这里需要实现从存储中加载数据的逻辑
        # 暂时返回空列表
        return []
    
    def _save_quality_metrics(self, dataset, metrics):
        """保存数据质量评分"""
        try:
            DataQualityMetric.objects.create(
                dataset=dataset,
                accuracy_score=metrics.get('accuracy_score', 0.0),
                completeness_score=metrics.get('completeness_score', 0.0),
                consistency_score=metrics.get('consistency_score', 0.0),
                total_score=metrics.get('total_score', 0.0)
            )
        except Exception as e:
            raise ValueError(f"保存质量评分失败: {str(e)}") 