from typing import Any, Optional, Dict, Union
import json
import re
from ..base import BaseNode, WorkflowContext

class JSONExtractorNode(BaseNode):
    """
    从文本中提取JSON的专用节点。
    支持从可能包含其他内容的文本中提取和验证JSON数据。
    """
    def __init__(
        self,
        node_id: str,
        node_name: str,
        input_variable_name: str,
        output_variable_name: str,
        schema: Optional[Dict] = None,
        default_value: Optional[Any] = None,
        raise_on_error: bool = True
    ):
        """
        初始化JSON提取器节点。

        Args:
            node_id (str): 节点ID。
            node_name (str): 节点名称。
            input_variable_name (str): 输入变量名称，包含可能的JSON文本。
            output_variable_name (str): 输出变量名称，存储提取的JSON。
            schema (Optional[Dict]): JSON Schema用于验证提取的数据（可选）。
            default_value (Optional[Any]): 提取失败时的默认值（可选）。
            raise_on_error (bool): 是否在提取失败时抛出异常。
        """
        super().__init__(node_id, node_name)
        self.input_variable_name = input_variable_name
        self.output_variable_name = output_variable_name
        self.schema = schema
        self.default_value = default_value
        self.raise_on_error = raise_on_error

    def _extract_json(self, text: str) -> Union[Dict, Any]:
        """
        从文本中提取JSON数据。

        Args:
            text (str): 可能包含JSON的文本。

        Returns:
            Union[Dict, Any]: 提取的JSON数据。

        Raises:
            ValueError: 如果无法提取有效的JSON且raise_on_error为True。
        """
        # 尝试查找 { 和 } 之间的内容
        start_pos = text.find('{')
        if start_pos == -1:
            if self.raise_on_error:
                raise ValueError("No JSON object found in the input text")
            return self.default_value
        
        # 从找到的 { 开始逐个字符扫描，计数括号的嵌套层级
        level = 0
        pos = start_pos
        
        while pos < len(text):
            char = text[pos]
            if char == '{':
                level += 1
            elif char == '}':
                level -= 1
                if level == 0:
                    # 找到匹配的结束括号
                    json_str = text[start_pos:pos + 1]
                    try:
                        data = json.loads(json_str)
                        # 如果提供了schema，验证数据
                        if self.schema:
                            from jsonschema import validate  # 可选依赖
                            validate(instance=data, schema=self.schema)
                        return data
                    except json.JSONDecodeError:
                        if self.raise_on_error:
                            raise ValueError("Invalid JSON format")
                        return self.default_value
                    except Exception as e:
                        if self.raise_on_error:
                            raise ValueError(f"JSON validation failed: {str(e)}")
                        return self.default_value
            pos += 1
        
        # 如果没有找到匹配的结束括号
        if self.raise_on_error:
            raise ValueError("No complete JSON object found in the input text")
        return self.default_value

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行JSON提取节点逻辑。

        Args:
            context (WorkflowContext): 当前工作流上下文。

        Returns:
            WorkflowContext: 包含提取的JSON的更新后上下文。

        Raises:
            ValueError: 如果输入变量不存在或JSON提取失败且raise_on_error为True。
        """
        print(f"--- Executing {self} ---")
        print(f"  Input Context: {context}")

        # 检查输入变量是否存在
        if self.input_variable_name not in context:
            raise ValueError(
                f"JSONExtractorNode '{self.node_id}': Required input variable "
                f"'{self.input_variable_name}' not found in context."
            )

        input_text = context[self.input_variable_name]
        
        try:
            # 提取JSON
            json_data = self._extract_json(input_text)
            print(f"  Extracted JSON: {json_data}")
        except Exception as e:
            if self.raise_on_error:
                print(f"  Error extracting JSON: {e}")
                raise
            json_data = self.default_value
            print(f"  Using default value: {json_data}")

        # 更新上下文
        updated_context = context.copy()
        updated_context[self.output_variable_name] = json_data
        
        print(f"  Output Context: {updated_context}")
        print(f"--- Finished {self} ---")
        
        return updated_context
