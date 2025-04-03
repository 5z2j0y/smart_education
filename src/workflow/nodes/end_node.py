from typing import List
from ..base import BaseNode, WorkflowContext

class EndNode(BaseNode):
    """
    工作流的结束节点。
    标记工作流执行完毕，并可能提取最终输出变量。
    """
    def __init__(self, node_id: str, node_name: str, input_variable_names: List[str]):
        """
        初始化结束节点。
        Args:
            node_id (str): 节点ID。
            node_name (str): 节点名称。
            input_variable_names (List[str]): 此节点期望从上下文中读取并可能作为最终结果的变量名称列表。
        """
        super().__init__(node_id, node_name)
        self.input_variable_names = input_variable_names

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行结束节点逻辑。
        主要职责是验证所需变量是否存在，并可能提取它们。

        Args:
            context (WorkflowContext): 包含所有执行结果的工作流上下文。

        Returns:
            WorkflowContext: 最终的上下文。
        """
        print(f"--- Executing {self} ---")
        print(f"  Input Context: {context}")
        final_output = {}
        
        for var_name in self.input_variable_names:
            if var_name not in context:
                raise ValueError(f"EndNode '{self.node_id}': Expected final variable '{var_name}' not found in context.")
            final_output[var_name] = context[var_name]

        print(f"  Final Workflow Variables Extracted: {final_output}")
        print(f"  Output Context: {context}")
        print(f"--- Finished {self} ---")
        # EndNode通常是最后一个节点，返回最终上下文
        return context
