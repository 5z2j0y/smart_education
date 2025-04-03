from typing import List, Any
from string import Template  # 使用Python标准库的Template进行变量替换
from ..base import BaseNode, WorkflowContext

class LLMNode(BaseNode):
    """
    与LLM交互的节点。
    根据输入上下文变量格式化系统提示词，调用LLM，并将结果存入输出变量。
    """
    def __init__(self, node_id: str, node_name: str,
                 system_prompt_template: str,
                 output_variable_name: str,
                 llm_client: Any): # 实际应为 BaseLLMClient 类型
        """
        初始化LLM节点。
        
        Args:
            node_id (str): 节点ID。
            node_name (str): 节点名称。
            system_prompt_template (str): 包含占位符（如 {variable_name}）的系统提示词模板。
            output_variable_name (str): LLM响应将存储在上下文中的变量名称。
            llm_client (Any): 用于调用LLM的客户端实例。
        """
        super().__init__(node_id, node_name)
        self.system_prompt_template = system_prompt_template
        self.output_variable_name = output_variable_name
        self.llm_client = llm_client
        
        # 从模板中提取变量名
        self.input_variable_names = self._extract_variables_from_template(system_prompt_template)

    def _extract_variables_from_template(self, template: str) -> List[str]:
        """从模板字符串中提取变量名"""
        # 简单方法：使用正则表达式直接查找{name}格式
        import re
        # 查找形如{variable_name}的模式
        matches = re.findall(r'\{([a-zA-Z0-9_]+)\}', template)
        # 返回唯一变量名列表
        return list(set(matches))

    def _format_prompt(self, context: WorkflowContext) -> str:
        """使用上下文中的变量值格式化提示词模板"""
        # 先检查所有必需变量是否存在
        for var_name in self.input_variable_names:
            if var_name not in context:
                raise ValueError(f"LLMNode '{self.node_id}': Required variable '{var_name}' not found in context for prompt formatting.")
        
        # 使用Python字符串格式化功能替换变量
        try:
            return self.system_prompt_template.format(**{k: v for k, v in context.items() 
                                                      if k in self.input_variable_names})
        except KeyError as e:
            raise ValueError(f"LLMNode '{self.node_id}': Error formatting prompt. Missing key: {e}")

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行LLM节点逻辑。
        1. 从上下文中获取所需输入变量。
        2. 格式化系统提示词。
        3. 调用LLM。
        4. 将LLM响应存入上下文。

        Args:
            context (WorkflowContext): 当前工作流上下文。

        Returns:
            WorkflowContext: 包含LLM响应的更新后上下文。
            
        Raises:
            ValueError: 如果上下文中缺少所需变量
            RuntimeError: 如果LLM调用失败
        """
        print(f"--- Executing {self} ---")
        print(f"  Input Context: {context}")

        # 1 & 2. 格式化提示词 (包含检查变量是否存在)
        formatted_prompt = self._format_prompt(context)
        print(f"  Formatted Prompt: {formatted_prompt}")

        # 3. 调用LLM
        try:
            llm_response = self.llm_client.invoke(formatted_prompt)
            print(f"  LLM Response: {llm_response}")
        except Exception as e:
            # 实际应用中应进行更细致的错误处理和重试逻辑
            print(f"  Error calling LLM: {e}")
            raise RuntimeError(f"LLMNode '{self.node_id}' failed during LLM invocation.") from e

        # 4. 更新上下文
        updated_context = context.copy()
        updated_context[self.output_variable_name] = llm_response
        print(f"  Output Context: {updated_context}")
        print(f"--- Finished {self} ---")

        return updated_context
