# 步骤1: 定义基础结构

本步骤我们将创建框架的基础结构，包括:
- `BaseNode` 抽象基类
- `WorkflowContext` 类型别名

## 任务

1. 创建 `BaseNode` 抽象类
2. 定义 `__init__` 和抽象方法 `execute`
3. 定义 `WorkflowContext` 类型别名

## 代码实现

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

# 定义工作流上下文类型别名
WorkflowContext = Dict[str, Any]

class BaseNode(ABC):
    """
    工作流中所有节点的抽象基类。
    """
    def __init__(self, node_id: str, node_name: str):
        """
        初始化基础节点。
        Args:
            node_id (str): 节点的唯一标识符。
            node_name (str): 节点的名称（方便理解）。
        """
        self.node_id = node_id
        self.node_name = node_name

    @abstractmethod
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行节点的核心逻辑。
        该方法必须被子类实现。

        Args:
            context (WorkflowContext): 当前的工作流上下文，包含所有可用变量。

        Returns:
            WorkflowContext: 更新后的工作流上下文。
                 (注意：为简单起见，这里返回更新后的context，
                  也可以设计成直接修改传入的context对象)
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.node_id}', name='{self.node_name}')"
```

## 验证

确保以下验证点通过：

1. **语法验证**：确保代码符合Python语法，特别是正确使用 `abc.ABC` 和 `abc.abstractmethod`。

2. **实例化测试**：尝试直接实例化 `BaseNode` 应该失败，因为它包含抽象方法。

    ```python
    try:
        node = BaseNode("test", "Test Node")
        print("错误：不应该能够实例化抽象类")
    except TypeError as e:
        print("正确：无法实例化抽象类:", e)
    ```

3. **子类测试**：创建一个简单的子类并实现 `execute` 方法，确认能够成功实例化。

    ```python
    class SimpleNode(BaseNode):
        def execute(self, context: WorkflowContext) -> WorkflowContext:
            print(f"执行 {self.node_name}")
            return context
    
    # 应该能成功创建实例
    node = SimpleNode("simple", "Simple Node")
    print(node)  # 应输出: SimpleNode(id='simple', name='Simple Node')
    
    # 测试执行方法
    context = {"test": "value"}
    result = node.execute(context)
    print(result)  # 应输出: {'test': 'value'}
    ```

完成这些验证后，基础结构的定义就完成了，可以继续进行下一步的实现。
