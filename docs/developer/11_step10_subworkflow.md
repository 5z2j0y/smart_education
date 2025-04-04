# 步骤10: 实现子工作流节点 (SubWorkflowNode)

本步骤我们将实现子工作流节点 `SubWorkflowNode`，它允许在主工作流中嵌套独立的工作流，提高模块化和可重用性。特别适合封装条件分支及其处理节点，并在处理完成后统一返回到主工作流的指定节点。

## 任务

1. 创建 `SubWorkflowNode` 类，继承自 `BaseNode`
2. 实现子工作流的封装和执行逻辑
3. 设计变量映射机制，解决主工作流和子工作流之间的变量命名空间问题
4. 实现子工作流退出节点检测机制
5. 设计单元测试检测上述步骤是否完成

## 设计思路

### 1. 子工作流节点设计

```python
from typing import List, Optional, Dict, Any
from ..base import BaseNode, WorkflowContext
from ..engine import Workflow

class SubWorkflowNode(BaseNode):
    """
    子工作流节点，封装完整的子工作流作为单个节点。
    
    允许在主工作流中嵌套独立的工作流，提高模块化和可维护性。
    支持封装条件分支及其处理节点，并在处理完成后统一返回到指定的下一节点。
    """
    def __init__(
        self,
        node_id: str,
        node_name: str,
        nodes: List[BaseNode],
        input_mapping: Optional[Dict[str, str]] = None,
        output_mapping: Optional[Dict[str, str]] = None,
        entry_node_id: Optional[str] = None,
        exit_node_id: Optional[str] = None,
        next_node_id: Optional[str] = None
    ):
        """初始化子工作流节点"""
        super().__init__(node_id, node_name)
        # 存储参数
        self.input_mapping = input_mapping or {}
        self.output_mapping = output_mapping or {}
        self.next_node_id = next_node_id
        self.entry_node_id = entry_node_id
        self.exit_node_id = exit_node_id
        
        # 验证节点列表并创建子工作流
        self._validate_nodes(nodes)
        self.workflow = Workflow(nodes)
        
        # 配置子工作流中的退出节点
        self._configure_exit_nodes(nodes)
```

### 2. 子工作流执行逻辑

```python
def execute(self, context: WorkflowContext) -> WorkflowContext:
    """执行子工作流节点"""
    print(f"--- Executing {self} ---")
    
    # 1. 准备子工作流的初始上下文(从主工作流映射变量)
    subworkflow_context = self._prepare_subworkflow_context(context)
    
    # 2. 执行子工作流
    try:
        # 使用自定义的节点监听器执行子工作流
        result_context = self.workflow.run(subworkflow_context, self._node_execution_listener)
        
        # 3. 将子工作流结果映射回主工作流上下文
        updated_context = self._map_results_to_main_context(context, result_context)
        
        return updated_context
    except Exception as e:
        print(f"  Subworkflow execution failed: {e}")
        raise RuntimeError(f"SubWorkflowNode '{self.node_id}' failed: {str(e)}") from e
```

### 3. 子工作流退出检测机制

```python
def _configure_exit_nodes(self, nodes: List[BaseNode]) -> None:
    """标记子工作流中的退出节点"""
    if self.exit_node_id:
        # 如果指定了出口节点，只配置该节点
        exit_node = next((node for node in nodes if node.node_id == self.exit_node_id), None)
        if exit_node:
            setattr(exit_node, '_is_subworkflow_exit', True)
    else:
        # 如果没有指定出口节点，则自动识别可能的出口节点
        for node in nodes:
            # 检查节点是否有明确的下一个节点
            has_next = (hasattr(node, 'next_node_id') and node.next_node_id) or \
                       (hasattr(node, 'next_node_selector') and node.next_node_selector)
            
            # 如果节点没有明确的下一个节点，且不是工作流的最后一个节点
            if not has_next and node is not nodes[-1]:
                setattr(node, '_is_subworkflow_exit', True)

def _node_execution_listener(self, node: BaseNode, current_context: WorkflowContext) -> None:
    """监听子工作流中节点的执行"""
    # 检查是否到达退出节点
    if hasattr(node, '_is_subworkflow_exit') and getattr(node, '_is_subworkflow_exit'):
        print(f"  Reached subworkflow exit node: {node.node_id}")
        # 标记子工作流完成
        current_context["_subworkflow_complete"] = True
```

### 4. 变量映射机制

```python
def _prepare_subworkflow_context(self, main_context: WorkflowContext) -> WorkflowContext:
    """准备子工作流的初始上下文"""
    subworkflow_context = {}
    
    # 映射输入变量
    for main_var, sub_var in self.input_mapping.items():
        if main_var in main_context:
            subworkflow_context[sub_var] = main_context[main_var]
        else:
            print(f"  Warning: Input variable '{main_var}' not found in main context")
    
    # 如果有入口节点，添加到上下文中
    if self.entry_node_id:
        subworkflow_context["next_node_id"] = self.entry_node_id
    
    return subworkflow_context

def _map_results_to_main_context(self, main_context: WorkflowContext, 
                                sub_context: WorkflowContext) -> WorkflowContext:
    """将子工作流结果映射回主工作流上下文"""
    updated_context = main_context.copy()
    
    # 映射输出变量
    for sub_var, main_var in self.output_mapping.items():
        if sub_var in sub_context:
            updated_context[main_var] = sub_context[sub_var]
        else:
            print(f"  Warning: Output variable '{sub_var}' not found in subworkflow result")
    
    # 设置下一个节点ID（如果有）
    if self.next_node_id:
        updated_context["next_node_id"] = self.next_node_id
    
    return updated_context
```

## 工作流引擎扩展

要支持子工作流中的退出节点检测，需要扩展工作流引擎：

```python
def run(self, initial_context: WorkflowContext, 
        node_listener: Optional[Callable[[BaseNode, WorkflowContext], None]] = None) -> WorkflowContext:
    """
    执行工作流，支持条件分支和线性执行。
    
    Args:
        initial_context (WorkflowContext): 工作流启动时的初始数据。
        node_listener (Callable, optional): 节点执行监听器，在每个节点执行后调用。
                                         可用于监控和控制工作流执行。
    """
    print("=== Starting Workflow Execution ===")
    current_context = initial_context.copy()  # 使用初始上下文的副本

    # 从第一个节点开始
    current_node = self.nodes[0]
    
    # 当仍有节点需要执行时继续
    while current_node:
        try:
            # 执行当前节点
            current_context = current_node.execute(current_context)
            
            # 如果提供了节点监听器，则调用它
            if node_listener:
                node_listener(current_node, current_context)
            
            # 检查是否需要提前退出子工作流
            if "_subworkflow_complete" in current_context:
                del current_context["_subworkflow_complete"]
                break
            
            # 确定下一个节点
            # ...现有的下一节点确定逻辑...
```

## 使用示例

### 封装心情分类和回应流程

```python
# 创建心情分类子工作流
mood_nodes = [
    # 心情分类节点
    ConditionalBranchNode(
        node_id="mood_classifier",
        node_name="User Mood Classifier",
        classes=[
            ClassDefinition(name="Positive", next_node_id="positive_response"),
            ClassDefinition(name="Negative", next_node_id="negative_response")
        ],
        input_variable_name="user_text",
        llm_client=llm_client
    ),
    
    # 积极心情回应节点
    LLMNode(
        node_id="positive_response",
        node_name="Positive Response",
        system_prompt_template="用户看起来心情不错！请以积极语气回应：{user_text}",
        output_variable_name="response",
        llm_client=llm_client
    ),
    
    # 消极心情回应节点
    LLMNode(
        node_id="negative_response",
        node_name="Negative Response",
        system_prompt_template="用户看起来心情不太好。请以温暖语气回应：{user_text}",
        output_variable_name="response",
        llm_client=llm_client
    )
]

# 创建子工作流节点
mood_processing = SubWorkflowNode(
    node_id="mood_workflow",
    node_name="Mood Processing Workflow",
    nodes=mood_nodes,
    input_mapping={"user_input": "user_text"},  # 主工作流→子工作流
    output_mapping={"response": "ai_response"},  # 子工作流→主工作流
    entry_node_id="mood_classifier",
    next_node_id="feedback_node"  # 子工作流结束后转到此节点
)

# 在主工作流中使用
main_workflow = Workflow([
    start_node,
    mood_processing,  # 封装的子工作流作为单个节点
    feedback_node,
    end_node
])
```

## 验证

为了验证 `SubWorkflowNode` 的功能，我们需要实施以下测试：

### 1. 基本封装测试

```python
def test_basic_subworkflow():
    """测试基本子工作流功能"""
    # 创建模拟LLM客户端
    mock_llm = MockLLMClient()
    
    # 创建子工作流节点
    start_node = StartNode("sub_start", "Sub Start", ["input_value"])
    process_node = LLMNode("sub_process", "Sub Process", 
                         system_prompt_template="Process: {input_value}",
                         output_variable_name="processed_value",
                         llm_client=mock_llm)
    end_node = EndNode("sub_end", "Sub End", ["processed_value"])
    
    # 创建子工作流节点
    sub_workflow = SubWorkflowNode(
        node_id="test_sub",
        node_name="Test SubWorkflow",
        nodes=[start_node, process_node, end_node],
        input_mapping={"main_input": "input_value"},
        output_mapping={"processed_value": "main_output"},
        next_node_id="next_main_node"
    )
    
    # 执行子工作流节点
    result = sub_workflow.execute({"main_input": "test data"})
    
    # 验证结果
    assert "main_output" in result
    assert result["main_output"] == mock_llm.get_response("Process: test data")
    assert result["next_node_id"] == "next_main_node"
```

### 2. 条件分支封装测试

```python
def test_conditional_branch_subworkflow():
    """测试封装条件分支的子工作流"""
    # 创建模拟LLM客户端，配置为返回特定分类
    mock_llm = MockLLMClient()
    mock_llm.set_classification_response("Positive")
    
    # 创建条件分支子工作流
    branch_node = ConditionalBranchNode(
        node_id="branch",
        node_name="Test Branch",
        classes=[
            ClassDefinition(name="Positive", next_node_id="pos_handler"),
            ClassDefinition(name="Negative", next_node_id="neg_handler")
        ],
        input_variable_name="query",
        llm_client=mock_llm
    )
    
    pos_node = LLMNode("pos_handler", "Positive Handler", 
                     system_prompt_template="Positive: {query}",
                     output_variable_name="response",
                     llm_client=mock_llm)
    
    neg_node = LLMNode("neg_handler", "Negative Handler", 
                     system_prompt_template="Negative: {query}",
                     output_variable_name="response",
                     llm_client=mock_llm)
    
    # 创建子工作流节点
    branch_workflow = SubWorkflowNode(
        node_id="branch_workflow",
        node_name="Branch Workflow",
        nodes=[branch_node, pos_node, neg_node],
        input_mapping={"user_query": "query"},
        output_mapping={"response": "final_response"},
        next_node_id="after_branch"
    )
    
    # 执行子工作流节点
    result = branch_workflow.execute({"user_query": "test query"})
    
    # 验证结果 - 应该执行正面处理节点
    assert "final_response" in result
    assert result["final_response"] == mock_llm.get_response("Positive: test query")
    assert result["next_node_id"] == "after_branch"
```

### 3. 自动出口节点检测测试

```python
def test_auto_exit_detection():
    """测试自动出口节点检测功能"""
    # 创建模拟LLM客户端
    mock_llm = MockLLMClient()
    
    # 创建子工作流节点，不指定exit_node_id
    node1 = StartNode("node1", "Node 1", ["input"])
    node2 = LLMNode("node2", "Node 2", 
                   system_prompt_template="Process: {input}",
                   output_variable_name="output",
                   llm_client=mock_llm)
    # 不指定next_node_id，应该自动被识别为出口节点
    
    # 创建子工作流节点
    auto_exit_workflow = SubWorkflowNode(
        node_id="auto_exit",
        node_name="Auto Exit Workflow",
        nodes=[node1, node2],
        input_mapping={"main_input": "input"},
        output_mapping={"output": "main_output"},
        next_node_id="main_next"
    )
    
    # 执行子工作流节点
    result = auto_exit_workflow.execute({"main_input": "test data"})
    
    # 验证结果
    assert "main_output" in result
    assert result["next_node_id"] == "main_next"
```

### 4. 入口节点指定测试

```python
def test_entry_node_specification():
    """测试指定入口节点功能"""
    # 创建模拟LLM客户端
    mock_llm = MockLLMClient()
    
    # 创建多个节点
    start_node = StartNode("start", "Start", ["input"])
    process1 = LLMNode("process1", "Process 1", 
                      system_prompt_template="Process1: {input}",
                      output_variable_name="output1",
                      llm_client=mock_llm)
    process2 = LLMNode("process2", "Process 2", 
                      system_prompt_template="Process2: {input}",
                      output_variable_name="output2",
                      llm_client=mock_llm)
    
    # 创建子工作流节点，指定process2为入口节点
    entry_workflow = SubWorkflowNode(
        node_id="entry_test",
        node_name="Entry Test Workflow",
        nodes=[start_node, process1, process2],
        input_mapping={"main_input": "input"},
        output_mapping={"output2": "main_output"},
        entry_node_id="process2",  # 跳过process1，直接从process2开始
        next_node_id="main_next"
    )
    
    # 执行子工作流节点
    result = entry_workflow.execute({"main_input": "test data"})
    
    # 验证结果 - 应该只执行process2
    assert "main_output" in result
    assert result["main_output"] == mock_llm.get_response("Process2: test data")
    # 确保没有执行process1
    assert "output1" not in result
```

## 总结

实现 `SubWorkflowNode` 使我们能够：

1. **模块化工作流**: 将相关功能组织为可重用组件
2. **封装复杂逻辑**: 隐藏子工作流内部细节，简化主工作流
3. **统一出口**: 子工作流中的不同分支最终会返回到主工作流中的同一节点
4. **变量命名空间隔离**: 通过映射机制避免变量名冲突
5. **支持灵活入口**: 可以指定子工作流的入口节点

这样的设计极大地增强了工作流框架的表达能力和可维护性，特别适合封装条件分支逻辑。