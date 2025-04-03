from abc import ABC, abstractmethod
from typing import Dict, Any, TypeAlias

# 工作流上下文类型定义 - 使用简单的字典存储变量
WorkflowContext: TypeAlias = Dict[str, Any]

class BaseNode(ABC):
    """
    工作流节点的抽象基类。
    所有具体的节点类型都应该继承此类并实现execute方法。
    """
    def __init__(self, node_id: str, node_name: str):
        """
        初始化节点。
        
        Args:
            node_id (str): 节点的唯一标识符
            node_name (str): 节点的描述性名称
        """
        self.node_id = node_id
        self.node_name = node_name
    
    @abstractmethod
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行节点的核心逻辑。
        
        Args:
            context (WorkflowContext): 输入的工作流上下文
            
        Returns:
            WorkflowContext: 处理后的工作流上下文
        """
        pass
    
    def __str__(self) -> str:
        """返回节点的字符串表示。"""
        return f"{self.__class__.__name__}(id='{self.node_id}', name='{self.node_name}')"
    
    def __repr__(self) -> str:
        """返回节点的详细字符串表示。"""
        return self.__str__()
