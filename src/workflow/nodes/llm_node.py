from typing import List, Any, Optional, Iterator, Callable
from ..base import BaseNode, WorkflowContext
import re

class LLMNode(BaseNode):
    """
    与LLM交互的节点。
    根据输入上下文变量格式化系统提示词，调用LLM，并将结果存入输出变量。
    """
    def __init__(self, node_id: str, node_name: str,
                 system_prompt_template: str,
                 output_variable_name: str,
                 llm_client: Any,
                 stream: bool = False,
                 stream_callback: Optional[Callable[[str], None]] = None,
                 next_node_id: Optional[str] = None,
                 next_node_selector: Optional[Callable[[WorkflowContext], str]] = None): 
        """
        初始化LLM节点。
        
        Args:
            node_id (str): 节点ID。
            node_name (str): 节点名称。
            system_prompt_template (str): 包含占位符（如 {variable_name}）的系统提示词模板。
            output_variable_name (str): LLM响应将存储在上下文中的变量名称。
            llm_client (Any): 用于调用LLM的客户端实例。
            stream (bool): 是否使用流式输出，默认为False。
            stream_callback (Optional[Callable[[str], None]]): 流式输出的回调函数，接收每个文本片段。
            next_node_id (Optional[str]): 直接指定下一个节点的ID，优先级低于next_node_selector。
            next_node_selector (Optional[Callable[[WorkflowContext], str]]): 
                基于上下文选择下一个节点ID的函数，优先级高于next_node_id。
        """
        super().__init__(node_id, node_name)
        self.system_prompt_template = system_prompt_template
        self.output_variable_name = output_variable_name
        self.llm_client = llm_client
        self.stream = stream
        self.stream_callback = stream_callback
        self.next_node_id = next_node_id
        self.next_node_selector = next_node_selector
        
        # 从模板中提取变量名
        self.input_variable_names = self._extract_variables_from_template(system_prompt_template)

    def _extract_variables_from_template(self, template: str) -> List[str]:
        """从模板字符串中提取变量名"""
        # 简单方法：使用正则表达式直接查找{name}格式
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

        # 3. 调用LLM（流式或非流式）
        try:
            if self.stream and hasattr(self.llm_client, 'invoke_stream'):
                # 流式调用
                full_response = ""
                print(f"  LLM Response (Streaming):", end="", flush=True)
                
                for text_chunk in self.llm_client.invoke_stream(formatted_prompt):
                    full_response += text_chunk
                    if self.stream_callback:
                        self.stream_callback(text_chunk)
                    else:
                        # 简单地打印出来，不换行
                        print(text_chunk, end="", flush=True)
                
                print()  # 完成后打印换行
                llm_response = full_response
            else:
                # 常规调用
                llm_response = self.llm_client.invoke(formatted_prompt)
                print(f"  LLM Response: {llm_response}")
                
        except Exception as e:
            print(f"  Error calling LLM: {e}")
            raise RuntimeError(f"LLMNode '{self.node_id}' failed during LLM invocation.") from e

        # 4. 更新上下文
        updated_context = context.copy()
        updated_context[self.output_variable_name] = llm_response
        print(f"  Output Context: {updated_context}")
        print(f"--- Finished {self} ---")

        return updated_context
