from .base_client import BaseLLMClient

class FakeLLMClient(BaseLLMClient):
    """
    用于测试的假LLM客户端。
    根据提示词中的关键词返回预定义的响应。
    """
    
    def invoke(self, prompt: str) -> str:
        """
        模拟调用LLM并返回预定义的响应。
        
        Args:
            prompt (str): 发送给模拟LLM的提示词
            
        Returns:
            str: 预定义的响应
        """
        print(f"    [Fake LLM] Received prompt: {prompt[:100]}...") # 打印部分提示词
        
        # 根据提示词中的关键词返回不同的模拟响应
        if "better user's query" in prompt:
            return "A detailed exploration of the concept of youth."
        elif "answer the query in detail" in prompt:
            return "Youth is often defined as the period between childhood and adult age..."
        else:
            return f"LLM Simulation: Processed prompt '{prompt[:50]}...'"
