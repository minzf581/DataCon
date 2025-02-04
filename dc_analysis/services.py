from typing import List, Dict
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, accuracy_score
from dc_core.models import Dataset, Project, AgentPerformance, DataRequirement

class DataAnalysisService:
    """数据分析服务"""
    
    def analyze_agent_performance(self, performance: AgentPerformance) -> Dict:
        """分析智能体性能"""
        # 分析性能指标
        metrics = performance.metrics
        dataset = performance.dataset
        project = performance.project
        
        # 分析数据集对性能的影响
        impact_analysis = self._analyze_dataset_impact(dataset, metrics)
        
        # 生成改进建议
        recommendations = self._generate_recommendations(impact_analysis)
        
        return {
            'impact_analysis': impact_analysis,
            'recommendations': recommendations
        }
    
    def generate_data_requirements(self, project: Project) -> List[DataRequirement]:
        """根据项目目标和智能体性能生成数据需求"""
        # 获取项目的性能记录
        performances = project.performances.all().order_by('-recorded_at')
        
        # 分析性能趋势
        performance_trend = self._analyze_performance_trend(performances)
        
        # 识别数据缺陷
        data_gaps = self._identify_data_gaps(project, performance_trend)
        
        # 生成数据需求
        requirements = []
        for gap in data_gaps:
            requirement = DataRequirement(
                project=project,
                description=gap['description'],
                priority=gap['priority']
            )
            requirements.append(requirement)
        
        # 批量创建数据需求
        DataRequirement.objects.bulk_create(requirements)
        
        return requirements
    
    def _analyze_dataset_impact(self, dataset: Dataset, metrics: Dict) -> Dict:
        """分析数据集对性能的影响"""
        impact_analysis = {
            'dataset_size_impact': self._analyze_size_impact(dataset.size, metrics),
            'quality_impact': self._analyze_quality_impact(dataset.quality_score, metrics),
            'performance_correlation': self._calculate_performance_correlation(dataset, metrics)
        }
        
        return impact_analysis
    
    def _generate_recommendations(self, impact_analysis: Dict) -> List[Dict]:
        """生成改进建议"""
        recommendations = []
        
        # 基于数据集大小的建议
        if impact_analysis['dataset_size_impact']['correlation'] > 0.7:
            recommendations.append({
                'type': 'data_size',
                'description': '增加数据集大小可能会提升性能',
                'priority': 'high'
            })
        
        # 基于数据质量的建议
        if impact_analysis['quality_impact']['correlation'] > 0.7:
            recommendations.append({
                'type': 'data_quality',
                'description': '提高数据质量可能会显著改善性能',
                'priority': 'high'
            })
        
        # 基于性能相关性的建议
        correlations = impact_analysis['performance_correlation']
        for metric, corr in correlations.items():
            if abs(corr) > 0.8:
                recommendations.append({
                    'type': 'performance_metric',
                    'description': f'指标 {metric} 与性能高度相关，建议优化相关数据',
                    'priority': 'medium'
                })
        
        return recommendations
    
    def _analyze_performance_trend(self, performances: List[AgentPerformance]) -> Dict:
        """分析性能趋势"""
        if not performances:
            return {}
            
        # 提取性能指标时间序列
        time_series = []
        for perf in performances:
            time_series.append({
                'timestamp': perf.recorded_at,
                'metrics': perf.metrics
            })
            
        # 计算趋势
        trend_analysis = {
            'overall_trend': self._calculate_trend(time_series),
            'metric_trends': self._calculate_metric_trends(time_series),
            'volatility': self._calculate_volatility(time_series)
        }
        
        return trend_analysis
    
    def _identify_data_gaps(self, project: Project, performance_trend: Dict) -> List[Dict]:
        """识别数据缺陷"""
        gaps = []
        
        # 分析性能趋势中的问题
        if performance_trend.get('overall_trend', {}).get('slope', 0) < 0:
            gaps.append({
                'description': json.dumps({
                    'type': 'web_api',
                    'url': 'https://api.example.com/data',
                    'reason': '性能下降趋势明显，需要新的训练数据'
                }),
                'priority': 8
            })
            
        # 分析各指标趋势
        metric_trends = performance_trend.get('metric_trends', {})
        for metric, trend in metric_trends.items():
            if trend['slope'] < -0.1:  # 指标显著下降
                gaps.append({
                    'description': json.dumps({
                        'type': 'web_api',
                        'url': f'https://api.example.com/data/{metric}',
                        'reason': f'指标 {metric} 性能下降，需要相关数据增强'
                    }),
                    'priority': 7
                })
        
        return gaps
    
    def _calculate_trend(self, time_series: List[Dict]) -> Dict:
        """计算整体趋势"""
        if not time_series:
            return {}
            
        # 提取时间和平均性能值
        times = np.array([(ts['timestamp'] - time_series[0]['timestamp']).total_seconds() 
                         for ts in time_series])
        values = np.array([np.mean(list(ts['metrics'].values())) for ts in time_series])
        
        # 计算线性回归
        slope, intercept = np.polyfit(times, values, 1)
        
        return {
            'slope': slope,
            'intercept': intercept,
            'direction': 'increasing' if slope > 0 else 'decreasing'
        }
    
    def _calculate_metric_trends(self, time_series: List[Dict]) -> Dict:
        """计算各指标的趋势"""
        if not time_series:
            return {}
            
        metric_trends = {}
        metrics = time_series[0]['metrics'].keys()
        
        for metric in metrics:
            times = np.array([(ts['timestamp'] - time_series[0]['timestamp']).total_seconds() 
                            for ts in time_series])
            values = np.array([ts['metrics'][metric] for ts in time_series])
            
            slope, intercept = np.polyfit(times, values, 1)
            metric_trends[metric] = {
                'slope': slope,
                'intercept': intercept,
                'direction': 'increasing' if slope > 0 else 'decreasing'
            }
        
        return metric_trends
    
    def _calculate_volatility(self, time_series: List[Dict]) -> float:
        """计算性能波动性"""
        if not time_series:
            return 0.0
            
        # 计算各指标的标准差
        metric_values = {}
        for ts in time_series:
            for metric, value in ts['metrics'].items():
                if metric not in metric_values:
                    metric_values[metric] = []
                metric_values[metric].append(value)
        
        # 计算平均波动性
        volatilities = [np.std(values) / np.mean(values) if np.mean(values) != 0 else 0 
                       for values in metric_values.values()]
        
        return np.mean(volatilities)
    
    def _analyze_size_impact(self, size: int, metrics: Dict) -> Dict:
        """分析数据集大小的影响"""
        # 这里应该实现更复杂的分析逻辑
        return {
            'correlation': 0.8,  # 示例值
            'optimal_size': size * 1.5
        }
    
    def _analyze_quality_impact(self, quality_score: float, metrics: Dict) -> Dict:
        """分析数据质量的影响"""
        # 这里应该实现更复杂的分析逻辑
        return {
            'correlation': 0.9,  # 示例值
            'quality_threshold': 0.8
        }
    
    def _calculate_performance_correlation(self, dataset: Dataset, metrics: Dict) -> Dict:
        """计算性能相关性"""
        # 这里应该实现更复杂的相关性分析
        return {
            'accuracy': 0.85,
            'loss': -0.75
        } 