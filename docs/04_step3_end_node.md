# 步骤3: 实现 EndNode

本步骤我们将实现工作流的终结节点 `EndNode`，它是工作流的终点，负责整理或提取最终结果。

## 任务

1. 创建 `EndNode` 类，继承自 `BaseNode`
2. 实现其 `__init__` 方法，接收需要从上下文提取的结果变量名列表
3. 实现 `execute` 方法，验证所需的结果变量是否存在于上下文中，并提取它们

## 代码实现

```python
from typing import List, Dict, Any
from base_node import BaseNode, WorkflowContext  # 假设我们已经在base_node.py中定义了这些

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
```

## 验证

确保以下验证点通过：

1. **实例化测试**：成功创建 `EndNode` 实例。

    ```python
    # 创建EndNode实例，期望从上下文中提取"result"变量
    end_node = EndNode("end", "End Node", ["result"])
    print(end_node)  # 应输出: EndNode(id='end', name='End Node')
    ```

2. **有效执行测试**：调用执行方法并提供包含所需变量的上下文。

    ```python
    # 提供包含所需变量的上下文
    context = {"result": "这是最终结果", "other_data": "其他数据"}
    result = end_node.execute(context)
    # 预期输出节点执行信息，提取结果变量，并返回完整上下文
    print(result)  # 应输出: {'result': '这是最终结果', 'other_data': '其他数据'}
    ```

3. **错误处理测试**：提供缺少所需变量的上下文，应该抛出异常。

    ```python
    try:
        # 提供缺少所需变量的上下文
        incomplete_context = {"other_data": "其他数据"}
        end_node.execute(incomplete_context)
        print("错误：应该抛出异常")
    except ValueError as e:
        print("正确：捕获到变量缺失异常:", e)
    ```

完成这些验证后，`EndNode` 的实现就完成了，可以继续进行下一步的实现。
