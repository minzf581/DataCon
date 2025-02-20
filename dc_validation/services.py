from typing import Dict, List, Any
import pandas as pd
import numpy as np
from dc_core.models import Dataset, DataQualityMetric

class DataQualityService:
    """数据质量评估服务"""
    
    def evaluate_dataset(self, dataset: Dataset) -> float:
        """评估数据集质量"""
        try:
            # 计算各项质量指标
            completeness = self._evaluate_completeness(self._load_dataset_data(dataset))
            consistency = self._evaluate_consistency(self._load_dataset_data(dataset))
            accuracy = self._evaluate_accuracy(self._load_dataset_data(dataset))
            
            # 计算总分
            total_score = (completeness + consistency + accuracy) / 3
            
            # 创建质量指标记录
            DataQualityMetric.objects.create(
                dataset=dataset,
                completeness_score=completeness,
                consistency_score=consistency,
                accuracy_score=accuracy,
                total_score=total_score
            )
            
            return total_score
        except Exception as e:
            print(f"质量评估失败: {str(e)}")
            return 0.0
    
    def _load_dataset(self, dataset: Dataset) -> pd.DataFrame:
        """加载数据集"""
        # 这里应该实现数据集加载逻辑
        # 可以从文件系统或数据库加载数据
        return pd.DataFrame()
    
    def _load_dataset_data(self, dataset: Dataset) -> pd.DataFrame:
        """加载数据集数据"""
        # 创建示例数据用于测试
        return pd.DataFrame({
            'A': range(10),
            'B': range(10, 20),
            'C': ['X', 'Y', 'Z'] * 3 + ['X']
        })
    
    def _evaluate_completeness(self, data: pd.DataFrame) -> float:
        """评估数据完整性"""
        if data.empty:
            return 0.0
        
        # 计算每列的完整性
        column_completeness = []
        for column in data.columns:
            non_null_count = data[column].count()
            total_count = len(data)
            column_completeness.append(non_null_count / total_count)
        
        # 计算整体完整性
        return np.mean(column_completeness) * 100
    
    def _evaluate_accuracy(self, data: pd.DataFrame) -> float:
        """评估数据准确性"""
        if data.empty:
            return 0.0
        
        accuracy_scores = []
        
        for column in data.columns:
            # 获取列的数据类型
            dtype = data[column].dtype
            
            # 对不同类型的数据进行准确性检查
            if pd.api.types.is_numeric_dtype(dtype):
                # 数值型数据：检查异常值
                accuracy_scores.append(self._check_numeric_accuracy(data[column]))
            elif pd.api.types.is_datetime64_dtype(dtype):
                # 日期型数据：检查日期有效性
                accuracy_scores.append(self._check_datetime_accuracy(data[column]))
            else:
                # 字符串数据：检查格式一致性
                accuracy_scores.append(self._check_string_accuracy(data[column]))
        
        return np.mean(accuracy_scores) * 100
    
    def _evaluate_consistency(self, data: pd.DataFrame) -> float:
        """评估数据一致性"""
        if data.empty:
            return 0.0
        
        consistency_scores = []
        
        # 检查数据格式一致性
        for column in data.columns:
            consistency_scores.append(self._check_format_consistency(data[column]))
        
        # 检查数值范围一致性
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        for column in numeric_columns:
            consistency_scores.append(self._check_range_consistency(data[column]))
        
        # 检查类别值一致性
        categorical_columns = data.select_dtypes(include=['object']).columns
        for column in categorical_columns:
            consistency_scores.append(self._check_category_consistency(data[column]))
        
        return np.mean(consistency_scores) * 100
    
    def _evaluate_timeliness(self, dataset: Dataset) -> float:
        """评估数据时效性"""
        # 计算数据的年龄（天数）
        age_days = (pd.Timestamp.now() - dataset.created_at.replace(tzinfo=None)).days
        
        # 设置时效性阈值（例如：30天）
        threshold_days = 30
        
        # 计算时效性得分
        timeliness_score = max(0, (threshold_days - age_days) / threshold_days)
        
        return timeliness_score * 100
    
    def _evaluate_relevance(self, dataset: Dataset) -> float:
        """评估数据相关性"""
        # 获取项目的性能记录
        performances = dataset.performances.all()
        
        if not performances:
            return 50.0  # 没有性能记录时返回中等分数
        
        # 计算平均性能提升
        performance_improvements = []
        for perf in performances:
            # 这里应该实现更复杂的性能提升计算逻辑
            improvement = sum(perf.metrics.values()) / len(perf.metrics)
            performance_improvements.append(improvement)
        
        # 归一化相关性得分
        relevance_score = np.mean(performance_improvements)
        normalized_score = min(100, max(0, relevance_score * 100))
        
        return normalized_score
    
    def _check_numeric_accuracy(self, series: pd.Series) -> float:
        """检查数值准确性"""
        # 计算Z分数
        z_scores = np.abs((series - series.mean()) / series.std())
        
        # 统计异常值比例（Z分数>3的视为异常值）
        outlier_ratio = (z_scores > 3).mean()
        
        return 1 - outlier_ratio
    
    def _check_datetime_accuracy(self, series: pd.Series) -> float:
        """检查日期准确性"""
        # 检查日期是否在合理范围内
        now = pd.Timestamp.now()
        min_date = pd.Timestamp('1970-01-01')
        
        valid_dates = series.between(min_date, now)
        return valid_dates.mean()
    
    def _check_string_accuracy(self, series: pd.Series) -> float:
        """检查字符串准确性"""
        # 检查字符串长度的一致性
        lengths = series.str.len()
        mean_length = lengths.mean()
        std_length = lengths.std()
        
        # 计算变异系数
        cv = std_length / mean_length if mean_length > 0 else 1
        
        return 1 - min(1, cv)
    
    def _check_format_consistency(self, series: pd.Series) -> float:
        """检查格式一致性"""
        # 对于非空值，检查数据格式的一致性
        non_null = series.dropna()
        if len(non_null) == 0:
            return 0.0
        
        # 获取最常见的格式
        if pd.api.types.is_numeric_dtype(series.dtype):
            # 对于数值型，检查小数位数
            decimals = non_null.astype(str).str.split('.').str[1].str.len()
            most_common_format = decimals.mode()[0]
            consistency_ratio = (decimals == most_common_format).mean()
        else:
            # 对于字符串，检查格式模式
            patterns = non_null.astype(str).str.len()
            most_common_format = patterns.mode()[0]
            consistency_ratio = (patterns == most_common_format).mean()
        
        return consistency_ratio
    
    def _check_range_consistency(self, series: pd.Series) -> float:
        """检查数值范围一致性"""
        # 计算四分位数范围
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        
        # 定义异常值范围
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # 计算在正常范围内的数据比例
        normal_range_ratio = series.between(lower_bound, upper_bound).mean()
        
        return normal_range_ratio
    
    def _check_category_consistency(self, series: pd.Series) -> float:
        """检查类别值一致性"""
        # 计算类别值的分布
        value_counts = series.value_counts(normalize=True)
        
        # 计算熵值（越低表示一致性越高）
        entropy = -np.sum(value_counts * np.log2(value_counts))
        max_entropy = np.log2(len(value_counts))
        
        # 归一化熵值到[0,1]区间
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        return 1 - normalized_entropy

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

    def _check_type_compatibility(self, actual_type: Any, expected_type: str) -> bool:
        """检查数据类型兼容性"""
        type_mappings = {
            'int': ['int64', 'int32'],
            'float': ['float64', 'float32'],
            'str': ['object'],
            'datetime': ['datetime64[ns]']
        }
        return str(actual_type) in type_mappings.get(expected_type, []) 