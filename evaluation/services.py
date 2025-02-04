from typing import Dict, Any
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from core.models import Dataset

class PerformanceEvaluator:
    """性能评估服务"""
    
    def __init__(self, original_dataset: Dataset, processed_dataset: Dataset):
        self.original_dataset = original_dataset
        self.processed_dataset = processed_dataset
        
    def evaluate_quality(self) -> Dict[str, Any]:
        """评估数据质量"""
        original_df = pd.read_csv(self.original_dataset.file_path)
        processed_df = pd.read_csv(self.processed_dataset.file_path)
        
        return {
            'completeness': self._evaluate_completeness(processed_df),
            'consistency': self._evaluate_consistency(original_df, processed_df),
            'statistics': self._calculate_statistics(processed_df)
        }
        
    def evaluate_model_performance(self, predictions: np.ndarray, true_labels: np.ndarray) -> Dict[str, float]:
        """评估模型性能"""
        return {
            'accuracy': accuracy_score(true_labels, predictions),
            'precision': precision_score(true_labels, predictions, average='weighted'),
            'recall': recall_score(true_labels, predictions, average='weighted'),
            'f1': f1_score(true_labels, predictions, average='weighted')
        }
        
    def _evaluate_completeness(self, df: pd.DataFrame) -> float:
        """评估数据完整性"""
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()
        return 1 - (missing_cells / total_cells)
        
    def _evaluate_consistency(self, original_df: pd.DataFrame, processed_df: pd.DataFrame) -> float:
        """评估数据一致性"""
        # 检查共同列的数据分布是否一致
        common_columns = set(original_df.columns) & set(processed_df.columns)
        consistency_scores = []
        
        for col in common_columns:
            orig_std = original_df[col].std()
            proc_std = processed_df[col].std()
            if orig_std != 0:
                consistency_scores.append(min(proc_std/orig_std, orig_std/proc_std))
                
        return np.mean(consistency_scores) if consistency_scores else 0.0
        
    def _calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算统计指标"""
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        
        stats = {}
        for col in numeric_columns:
            stats[col] = {
                'mean': df[col].mean(),
                'std': df[col].std(),
                'min': df[col].min(),
                'max': df[col].max()
            }
            
        return stats 