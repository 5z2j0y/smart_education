"""
子工作流节点实现，用于在主工作流中嵌套独立的工作流。
"""
from typing import List, Optional, Dict, Any, Callable
from ..base import BaseNode, WorkflowContext
from ..engine import Workflow

class SubWorkflowNode(BaseNode):
    """
    子工作流节点，封装完整的子工作流作为单个节点。
    
    允许在主工作流中嵌套独立的工作流，提高模块化和可维护性。
    支持封装条件分支及其处理节点，并在处理完成后统一返回到指定的下一节点。
    """
    def __init__(
        self,
        node_id: str,
        node_name: str,
        nodes: List[BaseNode],
        input_mapping: Optional[Dict[str, str]] = None,
        output_mapping: Optional[Dict[str, str]] = None,
        entry_node_id: Optional[str] = None,
        exit_node_id: Optional[str] = None,
        next_node_id: Optional[str] = None
    ):
        """
        初始化子工作流节点。
        
        Args:
            node_id (str): 节点唯一标识符。
            node_name (str): 节点名称，用于日志和调试。
            nodes (List[BaseNode]): 子工作流中的所有节点列表。
            input_mapping (Dict[str, str], optional): 主工作流到子工作流的变量映射字典。
                                                    格式为 {主工作流变量名: 子工作流变量名}。
            output_mapping (Dict[str, str], optional): 子工作流到主工作流的变量映射字典。
                                                     格式为 {子工作流变量名: 主工作流变量名}。
            entry_node_id (str, optional): 子工作流入口节点ID。如果指定，将从该节点开始执行，
                                          而不是从列表中的第一个节点开始。
            exit_node_id (str, optional): 子工作流出口节点ID。如果指定，将在该节点执行后
                                         返回到主工作流，不论后续还有什么节点。
            next_node_id (str, optional): 子工作流执行完毕后，主工作流中下一个要执行的节点ID。
        """
        super().__init__(node_id, node_name)
        # 存储参数
        self.input_mapping = input_mapping or {}
        self.output_mapping = output_mapping or {}
        self.next_node_id = next_node_id
        self.entry_node_id = entry_node_id
        self.exit_node_id = exit_node_id
        
        # 验证节点列表并创建子工作流
        self._validate_nodes(nodes)
        self.workflow = Workflow(nodes)
        
        # 配置子工作流中的退出节点
        self._configure_exit_nodes(nodes)
    
    def _validate_nodes(self, nodes: List[BaseNode]) -> None:
        """
        验证子工作流中的节点列表有效性。
        
        Args:
            nodes (List[BaseNode]): 待验证的节点列表。
            
        Raises:
            ValueError: 如果节点列表为空或存在重复的节点ID。
        """
        if not nodes:
            raise ValueError(f"SubWorkflowNode '{self.node_id}': Must contain at least one node.")
        
        # 检查节点ID唯一性
        node_ids = [node.node_id for node in nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError(f"SubWorkflowNode '{self.node_id}': Duplicate node IDs detected.")
        
        # 检查入口节点和出口节点是否存在（如果指定了的话）
        if self.entry_node_id and self.entry_node_id not in node_ids:
            raise ValueError(f"SubWorkflowNode '{self.node_id}': Entry node '{self.entry_node_id}' not found.")
        
        if self.exit_node_id and self.exit_node_id not in node_ids:
            raise ValueError(f"SubWorkflowNode '{self.node_id}': Exit node '{self.exit_node_id}' not found.")
    
    def _configure_exit_nodes(self, nodes: List[BaseNode]) -> None:
        """
        标记子工作流中的退出节点。
        
        Args:
            nodes (List[BaseNode]): 子工作流中的节点列表。
        """
        if self.exit_node_id:
            # 如果指定了出口节点，配置该节点
            exit_node = next((node for node in nodes if node.node_id == self.exit_node_id), None)
            if exit_node:
                setattr(exit_node, '_is_subworkflow_exit', True)
        else:
            # 自动识别分支处理节点作为退出节点
            # 查找所有没有在节点映射中作为前节点出现的节点
            # 这些可能是分支的终点节点
            from ..nodes.conditional_branch_node import ConditionalBranchNode
            
            # 构建所有next_node_id的集合
            next_ids = set()
            for node in nodes:
                # 从ConditionalBranchNode中收集所有目标节点ID
                if isinstance(node, ConditionalBranchNode):
                    for cls in node.classes:
                        next_ids.add(cls.next_node_id)
                    if node.default_class:
                        next_ids.add(node.default_class.next_node_id)
                # 收集普通节点的next_node_id
                elif hasattr(node, 'next_node_id') and node.next_node_id:
                    next_ids.add(node.next_node_id)
            
            # 标记所有被分支指向但自身没有下一节点的节点为退出节点
            for node in nodes:
                if node.node_id in next_ids and not (hasattr(node, 'next_node_id') and node.next_node_id):
                    print(f"  Auto-configuring exit node: {node.node_id}")
                    setattr(node, '_is_subworkflow_exit', True)
    
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行子工作流节点。
        
        将主工作流上下文中的变量映射到子工作流，执行子工作流，
        然后将子工作流的结果映射回主工作流上下文。
        
        Args:
            context (WorkflowContext): 主工作流的上下文。
            
        Returns:
            WorkflowContext: 更新后的主工作流上下文。
            
        Raises:
            RuntimeError: 如果子工作流执行失败。
        """
        print(f"--- Executing {self} ---")
        print(f"  Input Context: {context}")
        
        # 1. 准备子工作流的初始上下文(从主工作流映射变量)
        subworkflow_context = self._prepare_subworkflow_context(context)
        
        # 2. 执行子工作流
        try:
            # 使用自定义的节点监听器执行子工作流
            result_context = self.workflow.run(subworkflow_context, self._node_execution_listener)
            
            # 3. 将子工作流结果映射回主工作流上下文
            updated_context = self._map_results_to_main_context(context, result_context)
            
            print(f"  Output Context: {updated_context}")
            return updated_context
        except Exception as e:
            print(f"  Subworkflow execution failed: {e}")
            raise RuntimeError(f"SubWorkflowNode '{self.node_id}' failed: {str(e)}") from e
    
    def _prepare_subworkflow_context(self, main_context: WorkflowContext) -> WorkflowContext:
        """
        准备子工作流的初始上下文。
        
        将主工作流上下文中的变量按照映射关系拷贝到子工作流上下文中。
        
        Args:
            main_context (WorkflowContext): 主工作流上下文。
            
        Returns:
            WorkflowContext: 子工作流的初始上下文。
        """
        subworkflow_context = {}
        
        # 映射输入变量
        for main_var, sub_var in self.input_mapping.items():
            if main_var in main_context:
                subworkflow_context[sub_var] = main_context[main_var]
            else:
                print(f"  Warning: Input variable '{main_var}' not found in main context")
        
        # 如果有入口节点，添加到上下文中
        if self.entry_node_id:
            subworkflow_context["next_node_id"] = self.entry_node_id
        
        return subworkflow_context
    
    def _map_results_to_main_context(self, main_context: WorkflowContext, 
                                    sub_context: WorkflowContext) -> WorkflowContext:
        """
        将子工作流结果映射回主工作流上下文。
        
        Args:
            main_context (WorkflowContext): 主工作流原始上下文。
            sub_context (WorkflowContext): 子工作流执行后的上下文。
            
        Returns:
            WorkflowContext: 更新后的主工作流上下文。
        """
        updated_context = main_context.copy()
        
        # 映射输出变量
        for sub_var, main_var in self.output_mapping.items():
            if sub_var in sub_context:
                updated_context[main_var] = sub_context[sub_var]
            else:
                print(f"  Warning: Output variable '{sub_var}' not found in subworkflow result")
        
        # 设置下一个节点ID（如果有）
        if self.next_node_id:
            updated_context["next_node_id"] = self.next_node_id
        
        return updated_context
    
    def _node_execution_listener(self, node: BaseNode, current_context: WorkflowContext) -> None:
        """
        监听子工作流中节点的执行。
        
        用于检测是否到达了退出节点，如是则标记子工作流完成。
        
        Args:
            node (BaseNode): 刚执行完的节点。
            current_context (WorkflowContext): 当前上下文。
        """
        # 检查是否到达退出节点
        if hasattr(node, '_is_subworkflow_exit') and getattr(node, '_is_subworkflow_exit'):
            print(f"  Reached subworkflow exit node: {node.node_id}")
            # 标记子工作流完成
            current_context["_subworkflow_complete"] = True
