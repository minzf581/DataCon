from typing import Dict, Any
import pandas as pd
from core.models import Dataset

class DataProcessor:
    def __init__(self, dataset: Dataset):
        self.dataset = dataset
        
    def get_preview(self, rows: int = 5) -> Dict[str, Any]:
        """获取数据预览"""
        df = pd.read_csv(self.dataset.file_path)
        return {
            'columns': list(df.columns),
            'rows': df.head(rows).values.tolist(),
            'total_rows': len(df)
        }
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取基本统计信息"""
        df = pd.read_csv(self.dataset.file_path)
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        
        stats = {}
        for col in numeric_columns:
            stats[col] = {
                'mean': float(df[col].mean()),
                'std': float(df[col].std()),
                'min': float(df[col].min()),
                'max': float(df[col].max())
            }
        return stats
    
    def clean_data(self) -> pd.DataFrame:
        """数据清洗主函数"""
        df = pd.read_csv(self.dataset.file_path)
        
        # 基础清洗操作
        df = self._remove_duplicates(df)
        df = self._handle_missing_values(df)
        df = self._remove_noise(df)
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """去除重复数据"""
        return df.drop_duplicates()
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值"""
        # 数值型列使用均值填充
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        for col in numeric_columns:
            df[col].fillna(df[col].mean(), inplace=True)
            
        # 分类型列使用众数填充
        categorical_columns = df.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            df[col].fillna(df[col].mode()[0], inplace=True)
            
        return df
    
    def _remove_noise(self, df: pd.DataFrame) -> pd.DataFrame:
        """去除异常值"""
        numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
        for col in numeric_columns:
            # 使用IQR方法去除异常值
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            df = df[~((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR)))]
        
        return df 