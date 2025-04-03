# 步骤5: 实现 Workflow 执行器

本步骤我们将实现工作流执行器 `Workflow`，它负责按顺序执行节点列表，并管理上下文传递。

## 任务

1. 创建 `Workflow` 类
2. 实现 `__init__` 方法，接收节点列表
3. 实现 `run` 方法，按顺序执行节点并传递上下文

## 代码实现

```python
from typing import List, Dict, Any
from base_node import BaseNode, WorkflowContext  # 假设我们已经在base_node.py中定义了这些
from start_node import StartNode  # 用于类型检查

class Workflow:
    """
    线性工作流执行器。
    """
    def __init__(self, nodes: List[BaseNode]):
        """
        初始化工作流。
        Args:
            nodes (List[BaseNode]): 按执行顺序列出的节点列表。
                                   必须以StartNode开始，以EndNode结束（可选，但推荐）。
        """
        if not nodes:
            raise ValueError("Workflow must contain at least one node.")
        # 可以添加检查确保第一个是StartNode，最后一个是EndNode
        if not isinstance(nodes[0], StartNode):
             print("Warning: Workflow does not start with a StartNode.") # 或抛出错误
        # if not isinstance(nodes[-1], EndNode):
        #     print("Warning: Workflow does not end with an EndNode.") # EndNode非强制

        self.nodes = nodes

    def run(self, initial_context: WorkflowContext) -> WorkflowContext:
        """
        执行整个工作流。
        Args:
            initial_context (WorkflowContext): 工作流启动时的初始数据。
                                                对于StartNode，这里应包含其output_variable_names所需的值。

        Returns:
            WorkflowContext: 工作流执行完毕后的最终上下文。
        """
        print("=== Starting Workflow Execution ===")
        current_context = initial_context.copy() # 使用初始上下文的副本

        for node in self.nodes:
            try:
                # 每个节点执行并返回更新后的上下文
                current_context = node.execute(current_context)
            except Exception as e:
                print(f"!!! Workflow execution failed at node {node} !!!")
                print(f"Error: {e}")
                # 可以选择是停止执行还是记录错误并继续（如果设计允许）
                raise # 重新抛出异常，中断执行

        print("=== Workflow Execution Finished Successfully ===")
        return current_context
```

## 验证

确保以下验证点通过：

1. **实例化测试**：创建 `Workflow` 实例并传入节点列表。

    ```python
    from start_node import StartNode
    from end_node import EndNode
    
    # 创建简单的开始和结束节点
    start_node = StartNode("start", "Start Node", ["input_data"])
    end_node = EndNode("end", "End Node", ["input_data"])
    
    # 创建工作流
    workflow = Workflow([start_node, end_node])
    print("成功创建工作流实例")
    ```

2. **开始节点验证**：确保工作流会检查第一个节点是否为 `StartNode`。

    ```python
    # 测试没有StartNode的工作流
    try:
        # 创建两个EndNode
        end_node1 = EndNode("end1", "End Node 1", ["input_data"])
        end_node2 = EndNode("end2", "End Node 2", ["input_data"])
        
        # 创建没有StartNode的工作流
        invalid_workflow = Workflow([end_node1, end_node2])
        # 应该看到警告消息
        print("应该显示警告消息")
    except Exception as e:
        print("捕获到异常:", e)
    ```

3. **执行测试**：运行工作流并检查结果。

    ```python
    # 运行有效的工作流
    initial_context = {"input_data": "Hello, Workflow!"}
    result = workflow.run(initial_context)
    print("工作流执行结果:", result)
    # 应该返回原始上下文: {'input_data': 'Hello, Workflow!'}
    ```

4. **错误处理测试**：运行一个会失败的工作流，检查异常处理。

    ```python
    # 测试执行失败的工作流
    try:
        # 使用不满足StartNode要求的初始上下文
        empty_context = {}
        workflow.run(empty_context)
        print("错误：应该抛出异常")
    except Exception as e:
        print("正确：捕获到工作流执行异常:", e)
    ```

完成这些验证后，`Workflow` 执行器的实现就完成了，可以继续进行下一步的实现。
