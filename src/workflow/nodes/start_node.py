from typing import List, Optional
from ..base import BaseNode, WorkflowContext

class StartNode(BaseNode):
    """
    工作流的开始节点。
    负责验证初始输入是否存在于工作流上下文中。
    """
    def __init__(self, node_id: str, node_name: str, output_variable_names: List[str], 
                 next_node_id: Optional[str] = None):
        """
        初始化开始节点。
        
        Args:
            node_id (str): 节点ID。
            node_name (str): 节点名称。
            output_variable_names (List[str]): 此节点期望在上下文中发现的变量名称列表。
                                             这些变量的值应在工作流启动时提供。
            next_node_id (Optional[str]): 指定下一个节点的ID。如果不提供，则按工作流定义的顺序执行。
        """
        super().__init__(node_id, node_name)
        self.output_variable_names = output_variable_names
        self.next_node_id = next_node_id

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行开始节点逻辑。
        验证预期的变量是否存在于传入的上下文中。

        Args:
            context (WorkflowContext): 包含初始输入的工作流上下文。

        Returns:
            WorkflowContext: 验证后的上下文。
            
        Raises:
            ValueError: 如果上下文中缺少预期的初始变量。
        """
        print(f"--- Executing {self} ---")
        print(f"  Input Context: {context}")
        
        # 验证初始变量是否已提供
        for var_name in self.output_variable_names:
            if var_name not in context:
                raise ValueError(f"StartNode '{self.node_id}': Expected initial variable '{var_name}' not found in context.")
        
        # 如果有指定下一个节点ID，将其加入上下文
        updated_context = context.copy()
        if self.next_node_id:
            updated_context["next_node_id"] = self.next_node_id
            print(f"  Setting next_node_id to: {self.next_node_id}")
        
        print(f"  Output Context: {updated_context}")
        print(f"--- Finished {self} ---")
        
        return updated_context
