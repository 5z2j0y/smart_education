# 步骤8: 实现 JSONExtractorNode

本步骤我们将实现一个专门的JSON提取器节点 `JSONExtractorNode`，用于从LLM输出中提取JSON数据。这个节点将确保工作流中的JSON数据处理更可靠和标准化。

## 任务

1. 创建 `JSONExtractorNode` 类，继承自 `BaseNode`
2. 实现 JSON 提取和验证逻辑
3. 提供可配置的错误处理策略
4. 支持默认值和模式验证（可选）

## 代码实现

```python
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
        # 使用正则表达式查找可能的JSON部分
        json_pattern = r'\{(?:[^{}]|(?R))*\}'
        potential_jsons = re.finditer(json_pattern, text)
        
        for match in potential_jsons:
            try:
                json_str = match.group()
                data = json.loads(json_str)
                # 如果提供了schema，验证数据
                if self.schema:
                    from jsonschema import validate  # 可选依赖
                    validate(instance=data, schema=self.schema)
                return data
            except json.JSONDecodeError:
                continue
            except Exception as e:
                if self.raise_on_error:
                    raise ValueError(f"JSON validation failed: {str(e)}")
                continue

        # 如果没有找到有效的JSON
        if self.raise_on_error:
            raise ValueError("No valid JSON found in the input text")
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
```

## 验证

确保以下验证点通过：

1. **基本提取测试**：

```python
# 创建JSONExtractorNode实例
extractor = JSONExtractorNode(
    node_id="json_test",
    node_name="JSON Extractor",
    input_variable_name="llm_output",
    output_variable_name="parsed_json"
)

# 测试有效的JSON提取
context = {
    "llm_output": "Here's your data: { \"name\": \"Alice\", \"age\": 30 } Thank you!"
}
result = extractor.execute(context)
assert "parsed_json" in result
assert result["parsed_json"]["name"] == "Alice"
```

2. **模式验证测试**：

```python
# 创建带有schema的提取器
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "number"}
    },
    "required": ["name", "age"]
}

schema_extractor = JSONExtractorNode(
    node_id="schema_test",
    node_name="Schema JSON Extractor",
    input_variable_name="llm_output",
    output_variable_name="validated_json",
    schema=schema
)

# 测试有效数据
valid_context = {
    "llm_output": "{ \"name\": \"Bob\", \"age\": 25 }"
}
result = schema_extractor.execute(valid_context)
assert result["validated_json"]["name"] == "Bob"

# 测试无效数据（应该失败）
invalid_context = {
    "llm_output": "{ \"name\": \"Bob\" }"  # 缺少必需的age字段
}
try:
    schema_extractor.execute(invalid_context)
    assert False, "Should have raised an error"
except ValueError:
    assert True
```

3. **错误处理测试**：

```python
# 创建带有默认值的提取器
default_extractor = JSONExtractorNode(
    node_id="default_test",
    node_name="Default JSON Extractor",
    input_variable_name="llm_output",
    output_variable_name="json_data",
    default_value={"status": "error"},
    raise_on_error=False
)

# 测试无效输入
invalid_context = {
    "llm_output": "This is not JSON"
}
result = default_extractor.execute(invalid_context)
assert result["json_data"]["status"] == "error"
```

4. **工作流集成测试**：

```python
# 创建一个包含LLM节点和JSON提取器的工作流
workflow = Workflow([
    start_node,
    llm_node,
    json_extractor_node,
    end_node
])

# 运行工作流
initial_context = {"query": "以JSON格式返回用户信息"}
final_context = workflow.run(initial_context)
assert "parsed_json" in final_context
```

## 使用建议

1. **错误处理策略**：
   - 对于关键数据处理，设置 `raise_on_error=True`
   - 对于可选数据处理，提供 `default_value` 并设置 `raise_on_error=False`

2. **模式验证**：
   - 在处理结构化数据时，建议使用schema验证
   - 确保schema定义合理且完整

3. **性能考虑**：
   - 对于大文本输入，注意正则表达式的性能影响
   - 考虑添加超时机制防止复杂JSON解析阻塞

完成这些验证后，`JSONExtractorNode` 的实现就完成了，可以集成到现有工作流中使用。这个节点将大大提高处理LLM输出中JSON数据的可靠性和便利性。