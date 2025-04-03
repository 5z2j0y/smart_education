# 步骤2: 实现 StartNode

本步骤我们将实现工作流的起始节点 `StartNode`，它是工作流的入口点，负责初始化上下文或载入初始数据。

## 任务

1. 创建 `StartNode` 类，继承自 `BaseNode`
2. 实现其 `__init__` 方法，接收需要的初始变量名列表
3. 实现 `execute` 方法，验证所需的初始变量是否存在于上下文中

## 代码实现

```python
from typing import List, Dict, Any
from base_node import BaseNode, WorkflowContext  # 假设我们已经在base_node.py中定义了这些

class StartNode(BaseNode):
    """
    工作流的开始节点。
    负责将初始输入添加到工作流上下文中。
    """
    def __init__(self, node_id: str, node_name: str, output_variable_names: List[str]):
        """
        初始化开始节点。
        Args:
            node_id (str): 节点ID。
            node_name (str): 节点名称。
            output_variable_names (List[str]): 此节点将创建并添加到上下文中的变量名称列表。
                                             这些变量的值将在工作流启动时提供。
        """
        super().__init__(node_id, node_name)
        self.output_variable_names = output_variable_names

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行开始节点逻辑。
        在此简单实现中，它假设初始值已存在于传入的context中
        （由Workflow执行器在启动时放入）。
        主要职责是验证预期的变量是否存在。

        Args:
            context (WorkflowContext): 包含初始输入的工作流上下文。

        Returns:
            WorkflowContext: 未经修改或已验证的上下文。
        """
        print(f"--- Executing {self} ---")
        print(f"  Input Context: {context}")
        # 验证初始变量是否已由Workflow执行器提供
        for var_name in self.output_variable_names:
            if var_name not in context:
                # 实际应用中可能需要更健壮的错误处理
                raise ValueError(f"StartNode '{self.node_id}': Expected initial variable '{var_name}' not found in context.")
        print(f"  Output Context: {context}")
        print(f"--- Finished {self} ---")
        # 对于StartNode，通常只是传递上下文
        return context
```

## 验证

确保以下验证点通过：

1. **实例化测试**：成功创建 `StartNode` 实例。

    ```python
    # 创建StartNode实例，期望初始上下文中包含"user_query"变量
    start_node = StartNode("start", "Start Node", ["user_query"])
    print(start_node)  # 应输出: StartNode(id='start', name='Start Node')
    ```

2. **有效执行测试**：调用执行方法并提供包含所需变量的上下文。

    ```python
    # 提供包含所需变量的上下文
    context = {"user_query": "什么是人工智能？"}
    result = start_node.execute(context)
    # 预期输出节点执行信息并返回原始上下文
    print(result)  # 应输出: {'user_query': '什么是人工智能？'}
    ```

3. **错误处理测试**：提供缺少所需变量的上下文，应该抛出异常。

    ```python
    try:
        # 提供一个空上下文
        empty_context = {}
        start_node.execute(empty_context)
        print("错误：应该抛出异常")
    except ValueError as e:
        print("正确：捕获到变量缺失异常:", e)
    ```

完成这些验证后，`StartNode` 的实现就完成了，可以继续进行下一步的实现。
