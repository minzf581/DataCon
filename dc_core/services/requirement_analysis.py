import json
from typing import Dict
from openai import OpenAI
from django.conf import settings

class RequirementAnalysisService:
    """需求分析服务"""
    
    def __init__(self):
        """初始化服务"""
        self.openai_client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url="https://api.openai.com/v1"
        )
        
    def analyze_requirement(self, text: str) -> Dict:
        """分析需求文本"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # 使用更稳定的模型
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
    
    def validate_requirement(self, requirement: Dict) -> bool:
        """验证需求的完整性"""
        required_fields = {'data_type', 'timeframe', 'fields'}
        return all(field in requirement for field in required_fields)
        
    def _enrich_requirement(self, requirement: Dict) -> Dict:
        """增强需求信息"""
        if 'format' not in requirement:
            requirement['format'] = 'json'
        if 'frequency' not in requirement:
            requirement['frequency'] = 'once'
        return requirement 