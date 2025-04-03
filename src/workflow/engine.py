from typing import List
from .base import BaseNode, WorkflowContext
from .nodes.start_node import StartNode  # 用于类型检查

class Workflow:
    """
    线性工作流执行器。
    负责按顺序执行节点列表，并管理上下文传递。
    """
    def __init__(self, nodes: List[BaseNode]):
        """
        初始化工作流。
        
        Args:
            nodes (List[BaseNode]): 按执行顺序列出的节点列表。
                                   建议以StartNode开始，以EndNode结束。
        
        Raises:
            ValueError: 如果节点列表为空
        """
        if not nodes:
            raise ValueError("Workflow must contain at least one node.")
        
        # 检查确保第一个节点是StartNode
        if not isinstance(nodes[0], StartNode):
            print("Warning: Workflow does not start with a StartNode.")
        # EndNode检查是可选的，因为不是所有工作流都一定需要以EndNode结束
        # if not isinstance(nodes[-1], EndNode):
        #     print("Warning: Workflow does not end with an EndNode.")
        
        self.nodes = nodes

    def run(self, initial_context: WorkflowContext) -> WorkflowContext:
        """
        执行整个工作流。
        
        Args:
            initial_context (WorkflowContext): 工作流启动时的初始数据。
                                              对于StartNode，这里应包含其output_variable_names所需的值。

        Returns:
            WorkflowContext: 工作流执行完毕后的最终上下文。
            
        Raises:
            Exception: 如果节点执行过程中发生错误，会重新抛出异常
        """
        print("=== Starting Workflow Execution ===")
        current_context = initial_context.copy()  # 使用初始上下文的副本

        for node in self.nodes:
            try:
                # 每个节点执行并返回更新后的上下文
                current_context = node.execute(current_context)
            except Exception as e:
                print(f"!!! Workflow execution failed at node {node} !!!")
                print(f"Error: {e}")
                # 重新抛出异常，中断执行
                raise

        print("=== Workflow Execution Finished Successfully ===")
        return current_context
    
    def __str__(self) -> str:
        """返回工作流的字符串表示"""
        return f"Workflow(nodes={len(self.nodes)})"
