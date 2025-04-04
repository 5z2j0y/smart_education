from typing import List, Dict, Optional
from .base import BaseNode, WorkflowContext
from .nodes.start_node import StartNode  # 用于类型检查

class Workflow:
    """
    工作流执行器。
    负责执行节点，支持线性执行和条件分支。
    """
    def __init__(self, nodes: List[BaseNode]):
        """
        初始化工作流。
        
        Args:
            nodes (List[BaseNode]): 按顺序列出的节点列表。
                                   当节点没有定义next_node_selector时，按此顺序执行。
        
        Raises:
            ValueError: 如果节点列表为空
        """
        if not nodes:
            raise ValueError("Workflow must contain at least one node.")
        
        # 检查确保第一个节点是StartNode
        if not isinstance(nodes[0], StartNode):
            print("Warning: Workflow does not start with a StartNode.")
        
        self.nodes = nodes
        # 创建节点ID到节点实例的映射，用于条件分支
        self.node_map: Dict[str, BaseNode] = {node.node_id: node for node in nodes}
        
        # 创建默认的下一个节点映射（用于线性执行）
        self.next_node_map: Dict[str, BaseNode] = {}
        for i in range(len(nodes) - 1):
            self.next_node_map[nodes[i].node_id] = nodes[i + 1]

    def run(self, initial_context: WorkflowContext) -> WorkflowContext:
        """
        执行工作流，支持条件分支和线性执行。
        
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

        # 从第一个节点开始
        current_node = self.nodes[0]
        
        # 当仍有节点需要执行时继续
        while current_node:
            try:
                # 执行当前节点
                current_context = current_node.execute(current_context)
                
                # 确定下一个节点
                next_node = None
                next_node_id = None
                
                # 0. 首先检查上下文中是否已经指定了下一个节点ID
                if "next_node_id" in current_context:
                    next_node_id = current_context["next_node_id"]
                    # 从上下文中移除，避免影响后续节点
                    del current_context["next_node_id"]
                    print(f"  Branching: Using context-provided next node '{next_node_id}'")
                
                # 1. 如果上下文中没有指定，检查节点是否有next_node_selector
                if not next_node_id and hasattr(current_node, 'next_node_selector') and current_node.next_node_selector:
                    selector_result = current_node.next_node_selector(current_context)
                    if selector_result:
                        next_node_id = selector_result
                        print(f"  Branching: Selected next node '{next_node_id}' by selector")
                
                # 2. 如果没有通过selector获得节点ID，检查是否有静态指定的next_node_id
                if not next_node_id and hasattr(current_node, 'next_node_id') and current_node.next_node_id:
                    next_node_id = current_node.next_node_id
                    print(f"  Branching: Using statically defined next node '{next_node_id}'")
                
                # 3. 如果获得了节点ID，尝试从node_map中获取对应的节点
                if next_node_id:
                    if next_node_id in self.node_map:
                        next_node = self.node_map[next_node_id]
                    else:
                        raise ValueError(f"Node '{current_node.node_id}' referenced invalid next node ID: '{next_node_id}'")
                
                # 4. 如果没有通过分支获得下一个节点，使用默认的线性顺序
                if not next_node:
                    if current_node.node_id in self.next_node_map:
                        next_node = self.next_node_map[current_node.node_id]
                        print(f"  Sequential: Moving to next node '{next_node.node_id}'")
                    else:
                        print(f"  End of workflow: No next node defined after '{current_node.node_id}'")
                
                # 更新当前节点
                current_node = next_node
                
            except Exception as e:
                print(f"!!! Workflow execution failed at node {current_node} !!!")
                print(f"Error: {e}")
                # 重新抛出异常，中断执行
                raise

        print("=== Workflow Execution Finished Successfully ===")
        return current_context
    
    def __str__(self) -> str:
        """返回工作流的字符串表示"""
        return f"Workflow(nodes={len(self.nodes)})"
