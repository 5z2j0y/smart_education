from typing import Optional, Callable, Any
from ..base import BaseNode, WorkflowContext

class InputNode(BaseNode):
    """
    用于获取用户输入的交互节点。
    允许工作流在执行中暂停并获取用户输入。
    """
    def __init__(
        self,
        node_id: str,
        node_name: str,
        prompt_text: str,                        # 显示给用户的提示文本
        output_variable_name: str,               # 存储用户输入的变量名
        default_value: Optional[Any] = None,     # 可选的默认值
        validation_func: Optional[Callable[[str], bool]] = None,  # 可选的验证函数
        next_node_id: Optional[str] = None,      # 下一个节点ID
    ):
        super().__init__(node_id, node_name)
        self.prompt_text = prompt_text
        self.output_variable_name = output_variable_name
        self.default_value = default_value
        self.validation_func = validation_func
        self.next_node_id = next_node_id
        
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行输入节点逻辑：显示提示、获取输入、验证输入并更新上下文。
        
        Args:
            context (WorkflowContext): 当前工作流上下文
            
        Returns:
            WorkflowContext: 更新后的工作流上下文，包含用户输入
        """
        print(f"--- 执行 {self} ---")
        
        # 显示提示并获取用户输入
        print(f"\n{self.prompt_text}")
        
        # 获取有效输入
        valid_input = False
        user_input = None
        
        while not valid_input:
            user_input = input("> ")
            
            # 如果用户未输入且有默认值，使用默认值
            if not user_input and self.default_value is not None:
                user_input = self.default_value
                print(f"使用默认值: {user_input}")
            
            # 验证输入
            if self.validation_func and not self.validation_func(user_input):
                print("输入无效，请重新输入")
                continue
                
            valid_input = True
        
        # 更新上下文
        updated_context = context.copy()
        updated_context[self.output_variable_name] = user_input
        
        # 设置下一个节点ID（如果有）
        if self.next_node_id:
            updated_context["next_node_id"] = self.next_node_id
            
        print(f"  已保存输入到变量: {self.output_variable_name}")
        print(f"--- 完成 {self} ---")
        
        return updated_context
