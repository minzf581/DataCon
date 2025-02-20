from typing import Dict, Any
import pandas as pd
from dc_core.models import Dataset

class DataProcessor:
    def __init__(self, dataset: Dataset):
        self.dataset = dataset
        
    def get_preview(self, rows: int = 5) -> Dict[str, Any]:
        """获取数据预览"""
        try:
            # 创建示例数据用于测试
            df = pd.DataFrame({
                'A': range(10),
                'B': range(10, 20),
                'C': ['X', 'Y', 'Z'] * 3 + ['X']
            })
            return {
                'columns': list(df.columns),
                'rows': df.head(rows).values.tolist(),
                'total_rows': len(df)
            }
        except Exception as e:
            print(f"数据预览失败: {str(e)}")
            return {'error': str(e)}
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取基本统计信息"""
        try:
            # 创建示例数据用于测试
            df = pd.DataFrame({
                'A': range(10),
                'B': range(10, 20)
            })
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
        except Exception as e:
            print(f"统计计算失败: {str(e)}")
            return {'error': str(e)}
    
    def clean_data(self) -> pd.DataFrame:
        """数据清洗主函数"""
        try:
            # 创建示例数据用于测试
            df = pd.DataFrame({
                'A': range(10),
                'B': range(10, 20),
                'C': ['X', 'Y', 'Z'] * 3 + ['X']
            })
            
            # 基础清洗操作
            df = self._remove_duplicates(df)
            df = self._handle_missing_values(df)
            df = self._remove_noise(df)
            
            return df
        except Exception as e:
            print(f"数据清洗失败: {str(e)}")
            return pd.DataFrame()
    
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