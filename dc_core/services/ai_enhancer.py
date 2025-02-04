from typing import Dict, List, Any
import openai
from django.conf import settings
import json
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from dc_core.models import Dataset

class AIEnhancer:
    """AI增强服务"""
    
    def __init__(self, openai_client=None):
        """初始化AI增强器
        
        Args:
            openai_client: OpenAI客户端实例，如果为None则使用默认配置创建
        """
        from openai import OpenAI
        self.openai_client = openai_client or OpenAI(
            api_key=settings.OPENAI_API_KEY
        )
    
    def analyze_complex_requirements(self, text: str) -> Dict:
        """分析复杂需求"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个专业的数据需求分析专家，请帮助分析用户的数据需求。"},
                    {"role": "user", "content": f"请分析以下数据需求，并返回JSON格式的结构化信息：{text}"}
                ]
            )
            
            # 解析响应
            result = json.loads(response.choices[0].message.content)
            return self._enrich_requirement(result)
            
        except Exception as e:
            raise ValueError(f"需求分析失败: {str(e)}")
    
    def suggest_data_sources(self, requirement: Dict) -> List[Dict]:
        """推荐数据源"""
        try:
            # 构建提示
            prompt = f"""
            基于以下数据需求，推荐合适的数据源：
            数据类型: {requirement.get('data_type')}
            时间范围: {requirement.get('timeframe')}
            所需字段: {', '.join(requirement.get('fields', []))}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "你是一个数据源专家，请推荐最合适的数据源。"},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # 解析响应
            suggestions = json.loads(response.choices[0].message.content)
            return self._validate_sources(suggestions)
            
        except Exception as e:
            raise ValueError(f"数据源推荐失败: {str(e)}")
    
    def detect_anomalies(self, dataset: Dataset) -> Dict:
        """检测数据异常"""
        try:
            # 加载数据
            data = self._load_dataset_data(dataset)
            df = pd.DataFrame(data)
            
            # 数值列异常检测
            numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns
            if not numeric_columns.empty:
                # 标准化数据
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(df[numeric_columns])
                
                # 使用Isolation Forest检测异常
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                anomalies = iso_forest.fit_predict(scaled_data)
                
                # 统计异常
                anomaly_indices = [i for i, pred in enumerate(anomalies) if pred == -1]
                anomaly_records = df.iloc[anomaly_indices]
                
                return {
                    'anomaly_count': len(anomaly_indices),
                    'anomaly_percentage': len(anomaly_indices) / len(df) * 100,
                    'anomaly_records': anomaly_records.to_dict('records')
                }
            
            return {'anomaly_count': 0, 'anomaly_percentage': 0, 'anomaly_records': []}
            
        except Exception as e:
            raise ValueError(f"异常检测失败: {str(e)}")
    
    def extract_features(self, dataset: Dataset) -> Dict:
        """特征提取"""
        try:
            # 加载数据
            data = self._load_dataset_data(dataset)
            df = pd.DataFrame(data)
            
            features = {
                'basic_stats': self._calculate_basic_stats(df),
                'correlations': self._calculate_correlations(df),
                'distributions': self._analyze_distributions(df)
            }
            
            return features
            
        except Exception as e:
            raise ValueError(f"特征提取失败: {str(e)}")
    
    def _enrich_requirement(self, requirement: Dict) -> Dict:
        """丰富需求信息"""
        # 添加难度评估
        requirement['difficulty'] = self._estimate_difficulty(requirement)
        
        # 添加优先级建议
        requirement['priority'] = self._suggest_priority(requirement)
        
        # 添加时间估计
        requirement['estimated_time'] = self._estimate_time(requirement)
        
        return requirement
    
    def _estimate_difficulty(self, requirement: Dict) -> float:
        """估计需求难度"""
        difficulty_score = 0.0
        
        # 根据字段数量评估
        fields_count = len(requirement.get('fields', []))
        difficulty_score += min(fields_count * 0.1, 0.5)
        
        # 根据数据类型评估
        if requirement.get('data_type') in ['unstructured', 'mixed']:
            difficulty_score += 0.3
        
        # 根据时间范围评估
        if 'real-time' in requirement.get('timeframe', '').lower():
            difficulty_score += 0.2
        
        return min(difficulty_score, 1.0)
    
    def _suggest_priority(self, requirement: Dict) -> int:
        """建议优先级"""
        # 1-5的优先级，5最高
        priority = 3  # 默认中等优先级
        
        # 根据难度调整
        difficulty = requirement.get('difficulty', 0.5)
        if difficulty > 0.8:
            priority -= 1
        elif difficulty < 0.3:
            priority += 1
        
        # 根据时效性调整
        if 'real-time' in requirement.get('timeframe', '').lower():
            priority += 1
        
        return max(1, min(priority, 5))
    
    def _estimate_time(self, requirement: Dict) -> int:
        """估计完成时间（小时）"""
        base_time = 2  # 基础时间
        
        # 根据难度调整
        difficulty = requirement.get('difficulty', 0.5)
        time_estimate = base_time * (1 + difficulty)
        
        # 根据字段数量调整
        fields_count = len(requirement.get('fields', []))
        time_estimate += fields_count * 0.5
        
        return round(time_estimate)
    
    def _validate_sources(self, sources: List[Dict]) -> List[Dict]:
        """验证推荐的数据源"""
        validated_sources = []
        
        for source in sources:
            # 检查必需字段
            if all(key in source for key in ['name', 'url', 'type']):
                # 添加可用性评分
                source['availability_score'] = self._check_source_availability(source)
                validated_sources.append(source)
        
        return validated_sources
    
    def _check_source_availability(self, source: Dict) -> float:
        """检查数据源可用性"""
        # 这里可以添加实际的可用性检查逻辑
        return 0.95
    
    def _calculate_basic_stats(self, df: pd.DataFrame) -> Dict:
        """计算基本统计信息"""
        stats = {}
        
        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):
                stats[column] = {
                    'mean': df[column].mean(),
                    'std': df[column].std(),
                    'min': df[column].min(),
                    'max': df[column].max(),
                    'median': df[column].median()
                }
            else:
                stats[column] = {
                    'unique_count': df[column].nunique(),
                    'most_common': df[column].mode()[0] if not df[column].mode().empty else None,
                    'missing_count': df[column].isnull().sum()
                }
        
        return stats
    
    def _calculate_correlations(self, df: pd.DataFrame) -> Dict:
        """计算相关性"""
        numeric_df = df.select_dtypes(include=['int64', 'float64'])
        if not numeric_df.empty:
            return numeric_df.corr().to_dict()
        return {}
    
    def _analyze_distributions(self, df: pd.DataFrame) -> Dict:
        """分析数据分布"""
        distributions = {}
        
        for column in df.columns:
            if pd.api.types.is_numeric_dtype(df[column]):
                distributions[column] = {
                    'skewness': df[column].skew(),
                    'kurtosis': df[column].kurtosis(),
                    'histogram': df[column].value_counts(bins=10).to_dict()
                }
            else:
                distributions[column] = {
                    'value_counts': df[column].value_counts().to_dict()
                }
        
        return distributions
    
    def _load_dataset_data(self, dataset: Dataset) -> List[Dict]:
        """加载数据集数据"""
        # 这里需要实现从存储中加载数据的逻辑
        # 暂时返回空列表
        return [] 