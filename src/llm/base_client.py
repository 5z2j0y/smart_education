from abc import ABC, abstractmethod

class BaseLLMClient(ABC):
    """
    LLM客户端的抽象基类。
    定义了所有LLM客户端都需要实现的接口。
    """
    
    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """
        调用LLM并获取响应。
        
        Args:
            prompt (str): 发送给LLM的提示词
            
        Returns:
            str: LLM的文本响应
        """
        pass
