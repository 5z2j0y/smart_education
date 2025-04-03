from .base_client import BaseLLMClient
from openai import OpenAI

class OpenAIClient(BaseLLMClient):
    """
    OpenAI API客户端实现。
    通过OpenAI SDK调用OpenAI模型。
    """
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        初始化OpenAI客户端
        
        Args:
            api_key (str): OpenAI API密钥
            model (str): 要使用的模型名称
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def invoke(self, prompt: str) -> str:
        """
        调用OpenAI API发送请求并获取响应
        
        Args:
            prompt (str): 发送给模型的提示词
            
        Returns:
            str: 模型的文本响应
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API调用失败: {e}")
            raise
