from openai import OpenAI
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化客户端
client = OpenAI(
    api_key=os.getenv('OPENAI_API_KEY', ''),  # 从环境变量获取API密钥
    base_url="https://api.openai.com/v1"  # 显式设置API端点
)

try:
    # 创建一个简单的聊天完成
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # 尝试使用不同的模型
        messages=[
            {"role": "user", "content": "Say hello!"}
        ]
    )
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("Error:", str(e)) 