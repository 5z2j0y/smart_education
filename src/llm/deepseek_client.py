from .base_client import BaseLLMClient
from openai import OpenAI
from typing import Iterator, Optional, List, Dict, Any

class DeepSeekClient(BaseLLMClient):
    """
    DeepSeek API客户端实现。
    通过OpenAI SDK调用DeepSeek模型，使用OpenAI兼容的API。
    """
    
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        """
        初始化DeepSeek客户端
        
        Args:
            api_key (str): DeepSeek API密钥
            model (str): 要使用的模型名称，默认为deepseek-chat
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = model
    
    def invoke(self, prompt: str) -> str:
        """
        调用DeepSeek API发送请求并获取响应
        
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
            print(f"DeepSeek API调用失败: {e}")
            raise
    
    def invoke_stream(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> Iterator[str]:
        """
        调用DeepSeek API发送请求并获取流式响应
        
        Args:
            prompt (str): 发送给模型的提示词
            system_prompt (str): 系统提示词，设定AI助手的角色或行为
            
        Returns:
            Iterator[str]: 生成器，逐步返回模型的流式响应片段
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # 创建流式请求
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True  # 启用流式传输
            )
            
            # 逐步返回内容
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"DeepSeek API流式调用失败: {e}")
            raise
