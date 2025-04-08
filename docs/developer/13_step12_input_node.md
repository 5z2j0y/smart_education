# 步骤12: 实现InputNode - 用户输入节点

## 设计目标

为工作流提供一个灵活的用户交互点，使工作流能够在执行过程中暂停并获取用户输入，然后将输入保存到上下文中并继续执行。

## 设计思路

`InputNode` 作为工作流中的交互节点，需要：

1. **提示用户输入**：显示清晰的提示信息
2. **获取用户输入**：从控制台获取输入
3. **存储输入结果**：将输入内容保存到工作流上下文中
4. **提供验证机制**：可选的输入验证功能
5. **支持默认值**：当用户未输入时使用默认值

## 代码实现

```python
from src.workflow.base import BaseNode, WorkflowContext
from typing import Optional, Callable, Any

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
```

## 使用示例

```python
from src.workflow.nodes.input_node import InputNode

# 简单使用
input_node = InputNode(
    node_id="user_input",                      # 节点唯一标识符
    node_name="User Input",                    # 节点名称
    prompt_text="请输入您的问题:",             # 提示文本
    output_variable_name="user_question",      # 输出变量名
    next_node_id="llm_processor"               # 下一节点ID
)

# 使用验证函数
def validate_not_empty(text):
    return bool(text.strip())

validated_input = InputNode(
    node_id="validated_input",
    node_name="验证输入",
    prompt_text="请输入非空内容:",
    output_variable_name="validated_text",
    validation_func=validate_not_empty
)

# 带默认值
age_input = InputNode(
    node_id="age_input",
    node_name="年龄输入",
    prompt_text="请输入您的年龄(默认为18):",
    output_variable_name="user_age",
    default_value="18"
)
```

## 验证测试

以下是针对 `InputNode` 的单元测试代码:

```python
import unittest
from unittest.mock import patch
from src.workflow.nodes.input_node import InputNode

class TestInputNode(unittest.TestCase):
    
    def setUp(self):
        self.basic_node = InputNode(
            node_id="test_input",
            node_name="Test Input",
            prompt_text="输入测试:",
            output_variable_name="test_value"
        )
        
        self.node_with_default = InputNode(
            node_id="default_input",
            node_name="Default Input",
            prompt_text="带默认值输入:",
            output_variable_name="default_value",
            default_value="默认文本"
        )
        
        self.node_with_validation = InputNode(
            node_id="validated_input",
            node_name="Validated Input",
            prompt_text="请输入数字:",
            output_variable_name="number_value",
            validation_func=lambda x: x.isdigit()
        )
        
        self.node_with_next = InputNode(
            node_id="next_node_input",
            node_name="Input With Next",
            prompt_text="输入测试:",
            output_variable_name="test_value",
            next_node_id="next_test_node"
        )
    
    @patch('builtins.input', return_value="用户输入")
    def test_basic_input(self, mock_input):
        context = {}
        result = self.basic_node.execute(context)
        
        self.assertEqual(result["test_value"], "用户输入")
        self.assertNotIn("next_node_id", result)
    
    @patch('builtins.input', return_value="")
    def test_default_value(self, mock_input):
        context = {}
        result = self.node_with_default.execute(context)
        
        self.assertEqual(result["default_value"], "默认文本")
    
    @patch('builtins.input', side_effect=["abc", "123"])
    def test_validation(self, mock_input):
        context = {}
        result = self.node_with_validation.execute(context)
        
        self.assertEqual(result["number_value"], "123")
    
    @patch('builtins.input', return_value="用户输入")
    def test_next_node_id(self, mock_input):
        context = {}
        result = self.node_with_next.execute(context)
        
        self.assertEqual(result["test_value"], "用户输入")
        self.assertEqual(result["next_node_id"], "next_test_node")

if __name__ == '__main__':
    unittest.main()
```

## 设计优势

1. **简单直观**：接口设计简单明了，易于使用
2. **功能完备**：支持基本输入、验证、默认值等核心功能
3. **易于扩展**：可以通过自定义验证函数实现复杂的输入验证逻辑
4. **与工作流集成**：通过 `next_node_id` 保持与现有工作流引擎的兼容性

## 后续改进方向

1. **输入类型转换**：增加自动类型转换功能，如将输入直接转为 int 或其他类型
2. **多行输入模式**：支持获取多行文本输入
3. **秘密输入模式**：支持密码等不显示字符的输入
4. **交互增强**：添加颜色提示、格式化输出等

通过这个设计，工作流可以在任何需要用户干预的点暂停并获取输入，然后继续执行，极大增强了工作流的交互性和灵活性。