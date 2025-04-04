# 步骤11: 实现迭代工作流节点 (IterativeWorkflowNode)

本步骤我们将实现迭代工作流节点 `IterativeWorkflowNode`，它允许在主工作流中反复执行相同的子工作流，直到满足特定条件。这种设计对于需要多轮处理、循环遍历数据集或实现逐步改进的场景非常有用。

## 任务

1. 创建 `IterativeWorkflowNode` 类，继承自 `BaseNode`
2. 实现迭代逻辑，支持条件控制和最大迭代次数限制
3. 设计累积结果和中间状态管理机制
4. 支持迭代间上下文传递和变量更新
5. 设计单元测试验证上述功能

## 设计思路

### 1. 核心组件设计

1. **节点配置**
   - `condition_function`: 迭代继续条件的判断函数
   - `max_iterations`: 最大迭代次数限制
   - `input_mapping`: 主工作流到子工作流的变量映射
   - `output_mapping`: 子工作流到主工作流的变量映射
   - `iteration_mapping`: 迭代间的变量传递映射
   - `result_collector`: 结果收集配置

2. **结果收集模式**
   - `replace`: 只保留最后一次迭代结果
   - `append`: 将结果添加到列表
   - `merge`: 合并字典结果

3. **状态管理**
   - 迭代计数器管理
   - 中间状态存储与传递
   - 结果累积与更新机制

### 2. 工作流程设计

1. **初始化阶段**
   - 验证配置参数
   - 创建内部子工作流
   - 初始化状态管理器

2. **执行阶段**
   - 检查迭代条件
   - 准备子工作流上下文
   - 执行子工作流
   - 处理迭代结果
   - 更新主上下文

3. **完成阶段**
   - 整理最终结果
   - 清理临时状态
   - 设置下一节点

### 3. 关键实现特性

1. **变量映射机制**
   ```python
   # 示例配置
   input_mapping = {
       "main_text": "iteration_input",  # 主流程到子流程
       "main_config": "iteration_config"
   }
   
   iteration_mapping = {
       "iteration_output": "iteration_input"  # 迭代间传递
   }
   
   output_mapping = {
       "final_result": "main_result"  # 子流程到主流程
   }
   ```

2. **迭代控制**
   ```python
   def example_condition(context):
       """迭代控制示例"""
       # 达到质量阈值或最大次数时停止
       return (context.get("quality_score", 0) < 0.8 and 
               context.get("_iteration_count", 0) < 3)
   ```

### 4. 应用场景示例

1. **文本优化场景**
   - 逐步改进文本质量
   - 基于评分决定是否继续迭代
   - 收集每次改进的历史记录

2. **数据批处理场景**
   - 按批次处理大量数据
   - 跟踪处理进度
   - 汇总处理结果

3. **对话迭代场景**
   - 多轮对话管理
   - 状态追踪与更新
   - 对话历史维护

## 验证要点

1. **基础功能测试**
   - 迭代执行与终止
   - 最大次数限制
   - 变量映射正确性

2. **状态管理测试**
   - 迭代间数据传递
   - 上下文更新机制
   - 结果收集方式

3. **异常处理测试**
   - 迭代中断处理
   - 无效输入处理
   - 资源清理

## 总结

IterativeWorkflowNode 提供了以下核心能力：

1. **灵活的迭代控制**
   - 条件函数自定义
   - 最大次数限制
   - 动态终止机制

2. **完善的状态管理**
   - 迭代状态追踪
   - 变量映射系统
   - 结果累积策略

3. **场景适应性**
   - 支持多种迭代模式
   - 可配置的结果处理
   - 易于扩展和定制

这些特性使得该节点能够支持各类需要重复执行的复杂工作流场景，显著增强了框架的应用能力。

## 参考代码
# 设计迭代工作流节点 (IterativeWorkflowNode)

我需要参照子工作流节点的设计，为迭代工作流节点设计具体的实现代码。根据文档要求，IterativeWorkflowNode需要能够反复执行相同的子工作流，直到满足特定条件。

## 设计思路

### 1. 迭代工作流节点定义

```python
from typing import List, Optional, Dict, Any, Callable, Union, Literal
from ..base import BaseNode, WorkflowContext
from ..engine import Workflow

class IterativeWorkflowNode(BaseNode):
    """
    迭代工作流节点，用于重复执行子工作流直到满足条件。
    
    支持条件控制、最大迭代次数限制、结果累积和中间状态管理，
    适用于需要多轮处理、循环遍历或渐进改进的场景。
    """
    def __init__(
        self,
        node_id: str,
        node_name: str,
        nodes: List[BaseNode],
        condition_function: Callable[[WorkflowContext], bool],
        max_iterations: int = 10,
        input_mapping: Optional[Dict[str, str]] = None,
        output_mapping: Optional[Dict[str, str]] = None,
        iteration_mapping: Optional[Dict[str, str]] = None,
        result_collection_mode: Literal["replace", "append", "merge"] = "replace",
        result_variable: Optional[str] = None,
        next_node_id: Optional[str] = None
    ):
        """初始化迭代工作流节点"""
        super().__init__(node_id, node_name)
        # 存储参数
        self.input_mapping = input_mapping or {}
        self.output_mapping = output_mapping or {}
        self.iteration_mapping = iteration_mapping or {}
        self.next_node_id = next_node_id
        self.condition_function = condition_function
        self.max_iterations = max_iterations
        self.result_collection_mode = result_collection_mode
        self.result_variable = result_variable
        
        # 验证节点列表并创建子工作流
        self._validate_nodes(nodes)
        self.workflow = Workflow(nodes)
        
        # 验证结果收集配置
        self._validate_result_collection()
```

### 2. 执行逻辑实现

```python
def execute(self, context: WorkflowContext) -> WorkflowContext:
    """执行迭代工作流节点"""
    print(f"--- Executing {self} ---")
    
    # 初始化迭代状态
    iteration_count = 0
    iteration_context = self._prepare_initial_context(context)
    results = []
    
    # 执行迭代循环
    while self._should_continue(iteration_context, iteration_count):
        print(f"  Starting iteration {iteration_count + 1}")
        
        try:
            # 执行子工作流
            result_context = self.workflow.run(iteration_context)
            
            # 处理当前迭代结果
            if self.result_variable and self.result_variable in result_context:
                result = result_context[self.result_variable]
                self._collect_result(results, result)
                print(f"  Collected result for iteration {iteration_count + 1}")
            
            # 准备下一次迭代的上下文
            iteration_context = self._prepare_next_iteration(result_context)
            
            # 更新迭代计数
            iteration_count += 1
            # 在上下文中保存迭代计数，供条件函数使用
            iteration_context["_iteration_count"] = iteration_count
            
        except Exception as e:
            print(f"  Iteration {iteration_count + 1} failed: {e}")
            raise RuntimeError(f"IterativeWorkflowNode '{self.node_id}' failed at iteration {iteration_count + 1}: {str(e)}") from e
    
    print(f"  Completed after {iteration_count} iterations")
    
    # 将最终结果映射回主上下文
    updated_context = self._map_results_to_main_context(context, iteration_context, results)
    
    return updated_context
```

### 3. 迭代控制和状态管理

```python
def _should_continue(self, context: WorkflowContext, iteration_count: int) -> bool:
    """判断是否应继续迭代"""
    # 检查最大迭代次数
    if iteration_count >= self.max_iterations:
        print(f"  Reached maximum iterations limit ({self.max_iterations})")
        return False
    
    # 应用用户定义的条件函数
    try:
        should_continue = self.condition_function(context)
        if not should_continue:
            print("  Iteration condition evaluated to False, stopping iterations")
        return should_continue
    except Exception as e:
        print(f"  Error in condition function: {e}")
        # 条件函数出错时默认停止迭代
        return False

def _prepare_initial_context(self, main_context: WorkflowContext) -> WorkflowContext:
    """准备第一次迭代的初始上下文"""
    iteration_context = {}
    
    # 映射输入变量
    for main_var, iter_var in self.input_mapping.items():
        if main_var in main_context:
            iteration_context[iter_var] = main_context[main_var]
        else:
            print(f"  Warning: Input variable '{main_var}' not found in main context")
    
    # 初始化迭代计数
    iteration_context["_iteration_count"] = 0
    
    return iteration_context

def _prepare_next_iteration(self, current_context: WorkflowContext) -> WorkflowContext:
    """准备下一次迭代的上下文"""
    next_context = {}
    
    # 应用迭代间变量映射
    for src_var, dest_var in self.iteration_mapping.items():
        if src_var in current_context:
            next_context[dest_var] = current_context[src_var]
        else:
            print(f"  Warning: Iteration variable '{src_var}' not found for mapping")
    
    # 保留特殊控制变量
    if "_iteration_count" in current_context:
        next_context["_iteration_count"] = current_context["_iteration_count"]
    
    return next_context
```

### 4. 结果收集和处理机制

```python
def _validate_result_collection(self):
    """验证结果收集配置"""
    valid_modes = ["replace", "append", "merge"]
    if self.result_collection_mode not in valid_modes:
        raise ValueError(f"Invalid result collection mode: {self.result_collection_mode}. Must be one of {valid_modes}")
    
    if self.result_collection_mode in ["append", "merge"] and not self.result_variable:
        raise ValueError(f"Result variable must be specified when using '{self.result_collection_mode}' collection mode")

def _collect_result(self, results: list, result: Any) -> None:
    """根据收集模式处理结果"""
    if self.result_collection_mode == "replace":
        # 清空之前的结果并添加新结果
        results.clear()
        results.append(result)
    elif self.result_collection_mode == "append":
        # 将新结果添加到列表中
        results.append(result)
    elif self.result_collection_mode == "merge" and isinstance(result, dict):
        # 合并字典结果
        merged_result = {}
        # 如果已有结果，取最后一个作为基础
        if results:
            if isinstance(results[-1], dict):
                merged_result = results[-1].copy()
        # 合并新结果
        merged_result.update(result)
        
        # 更新或添加合并结果
        if results:
            results[-1] = merged_result
        else:
            results.append(merged_result)
    else:
        # 对于不是字典的数据，当使用merge模式时，退化为append
        results.append(result)

def _map_results_to_main_context(self, main_context: WorkflowContext, 
                                final_iter_context: WorkflowContext,
                                collected_results: list) -> WorkflowContext:
    """将迭代结果映射回主工作流上下文"""
    updated_context = main_context.copy()
    
    # 映射最终迭代的输出变量
    for iter_var, main_var in self.output_mapping.items():
        if iter_var in final_iter_context:
            updated_context[main_var] = final_iter_context[iter_var]
        else:
            print(f"  Warning: Output variable '{iter_var}' not found in final iteration context")
    
    # 添加收集的结果（如果有）
    if self.result_variable and collected_results:
        if self.result_collection_mode == "replace":
            # 只使用最后一个结果
            updated_context[self.result_variable] = collected_results[0]
        elif self.result_collection_mode == "append":
            # 使用完整的结果列表
            updated_context[self.result_variable] = collected_results
        elif self.result_collection_mode == "merge" and collected_results:
            # 使用合并后的结果
            updated_context[self.result_variable] = collected_results[-1]
    
    # 添加迭代次数信息
    if "_iteration_count" in final_iter_context:
        updated_context["_iterations_completed"] = final_iter_context["_iteration_count"]
    
    # 设置下一个节点ID（如果有）
    if self.next_node_id:
        updated_context["next_node_id"] = self.next_node_id
    
    return updated_context
```

### 5. 节点验证方法

```python
def _validate_nodes(self, nodes: List[BaseNode]) -> None:
    """验证节点列表"""
    if not nodes:
        raise ValueError("IterativeWorkflowNode requires at least one node")
    
    # 确保节点ID唯一
    node_ids = [node.node_id for node in nodes]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("Duplicate node IDs found in subworkflow nodes")
    
    # 检查节点类型和结构（可以添加更多验证）
    from ..nodes.start_node import StartNode
    if not isinstance(nodes[0], StartNode):
        print("  Warning: First node in iterative workflow is not a StartNode")
```

## 使用示例

### 文本优化迭代示例

```python
# 定义迭代条件函数
def quality_check(context):
    """根据文本质量评分决定是否继续迭代"""
    quality_score = context.get("quality_score", 0)
    iteration_count = context.get("_iteration_count", 0)
    
    # 如果质量分数低于0.8且迭代次数少于3次，继续迭代
    return quality_score < 0.8 and iteration_count < 3

# 创建迭代工作流节点
text_improver = IterativeWorkflowNode(
    node_id="text_improver",
    node_name="Iterative Text Improvement",
    nodes=[
        StartNode("start", "Start", ["text_draft"]),
        LLMNode("improve", "Improve Text", 
               system_prompt_template="改进以下文本，让它更清晰、更专业：{text_draft}",
               output_variable_name="improved_text",
               llm_client=llm_client),
        LLMNode("evaluate", "Evaluate Quality", 
               system_prompt_template="""
               评估以下文本的质量，返回0到1之间的分数，格式为JSON：
               {improved_text}
               
               返回格式: {"quality_score": 0.75, "feedback": "改进建议..."}
               """,
               output_variable_name="evaluation",
               llm_client=llm_client)
    ],
    condition_function=quality_check,
    max_iterations=5,
    input_mapping={"initial_draft": "text_draft"},
    iteration_mapping={"improved_text": "text_draft"},
    output_mapping={"improved_text": "final_text", "evaluation": "final_evaluation"},
    result_collection_mode="append",
    result_variable="improvement_history",
    next_node_id="publish_node"
)

# 使用示例
workflow = Workflow([
    start_node,
    text_improver,  # 迭代文本优化节点
    publish_node,
    end_node
])

# 执行工作流
result = workflow.run({
    "initial_draft": "人工智能是计算机科学的一个分支。它尝试理解智能的本质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。"
})

# 结果中将包含:
# - final_text: 最终优化后的文本
# - final_evaluation: 最终文本的质量评估
# - improvement_history: 所有迭代版本的列表
# - _iterations_completed: 实际完成的迭代次数
```

## 验证测试

### 1. 基本迭代功能测试

```python
def test_basic_iteration():
    """测试基本迭代功能"""
    # 创建模拟LLM客户端
    mock_llm = MockLLMClient()
    
    # 设置模拟响应
    mock_llm.set_response_sequence([
        "Improved text 1",  # 第一次迭代的改进文本
        '{"quality_score": 0.5, "feedback": "Still needs work"}',  # 第一次评估
        "Improved text 2",  # 第二次迭代
        '{"quality_score": 0.9, "feedback": "Much better"}',  # 第二次评估达到阈值
    ])
    
    # 定义迭代条件
    def iteration_condition(context):
        # 从评估结果中提取质量分数
        if "evaluation" in context:
            try:
                eval_data = json.loads(context["evaluation"])
                return eval_data.get("quality_score", 0) < 0.8
            except:
                return False
        return True  # 首次迭代时没有评估结果，默认继续
    
    # 创建节点
    start_node = StartNode("iter_start", "Iteration Start", ["content"])
    improve_node = LLMNode("improve", "Improve Content", 
                          system_prompt_template="Improve: {content}",
                          output_variable_name="improved_content",
                          llm_client=mock_llm)
    evaluate_node = LLMNode("evaluate", "Evaluate Content", 
                           system_prompt_template="Evaluate: {improved_content}",
                           output_variable_name="evaluation",
                           llm_client=mock_llm)
    
    # 创建迭代工作流节点
    iterative_node = IterativeWorkflowNode(
        node_id="iterative_test",
        node_name="Test Iteration",
        nodes=[start_node, improve_node, evaluate_node],
        condition_function=iteration_condition,
        max_iterations=5,
        input_mapping={"input_text": "content"},
        iteration_mapping={"improved_content": "content"},
        output_mapping={"improved_content": "final_content", "evaluation": "final_evaluation"},
        result_collection_mode="append",
        result_variable="iteration_history",
        next_node_id="next_main_node"
    )
    
    # 执行节点
    result = iterative_node.execute({"input_text": "Initial text"})
    
    # 验证结果
    assert result["final_content"] == "Improved text 2"
    assert "_iterations_completed" in result
    assert result["_iterations_completed"] == 2
    assert "iteration_history" in result
    assert len(result["iteration_history"]) == 2
    assert result["next_node_id"] == "next_main_node"
```

### 2. 最大迭代限制测试

```python
def test_max_iterations_limit():
    """测试最大迭代次数限制"""
    # 创建模拟LLM客户端
    mock_llm = MockLLMClient()
    
    # 设置模拟响应 - 每次都返回相同的低质量结果
    mock_llm.set_response_sequence([
        "Attempt 1", '{"quality_score": 0.3}',
        "Attempt 2", '{"quality_score": 0.4}',
        "Attempt 3", '{"quality_score": 0.5}',
        "Attempt 4", '{"quality_score": 0.6}',  # 不应到达此处
    ])
    
    # 定义总是返回True的条件（迭代永不停止）
    def always_continue(context):
        return True
    
    # 创建节点和迭代工作流
    # ...与上例类似...
    
    # 设置最大迭代次数为3
    iterative_node = IterativeWorkflowNode(
        # ...其他参数与上例类似...
        condition_function=always_continue,
        max_iterations=3,  # 最多执行3次迭代
        # ...其他参数...
    )
    
    # 执行节点
    result = iterative_node.execute({"input_text": "Initial text"})
    
    # 验证结果 - 应该在达到最大迭代次数后停止
    assert result["_iterations_completed"] == 3
    assert result["final_content"] == "Attempt 3"
```

### 3. 结果收集模式测试

```python
def test_result_collection_modes():
    """测试不同的结果收集模式"""
    # 创建模拟LLM客户端
    mock_llm = MockLLMClient()
    
    # 设置模拟响应
    mock_llm.set_response_sequence([
        # 替换模式测试
        '{"key": "value1"}', '{"quality": 0.5}',
        '{"key": "value2"}', '{"quality": 0.9}',
        
        # 追加模式测试
        '{"key": "append1"}', '{"quality": 0.5}',
        '{"key": "append2"}', '{"quality": 0.9}',
        
        # 合并模式测试
        '{"key1": "merge1"}', '{"quality": 0.5}',
        '{"key2": "merge2"}', '{"quality": 0.9}',
    ])
    
    # 定义条件函数
    def stop_after_two(context):
        return context.get("_iteration_count", 0) < 2
    
    # 测试替换模式
    replace_node = IterativeWorkflowNode(
        # ...基本参数...
        result_collection_mode="replace",
        result_variable="result",
        # ...其他参数...
    )
    replace_result = replace_node.execute({"input": "test"})
    assert replace_result["result"] == {"key": "value2"}  # 只保留最后一个
    
    # 测试追加模式
    append_node = IterativeWorkflowNode(
        # ...基本参数...
        result_collection_mode="append",
        result_variable="results",
        # ...其他参数...
    )
    append_result = append_node.execute({"input": "test"})
    assert len(append_result["results"]) == 2  # 包含两次迭代结果
    assert append_result["results"][0] == {"key": "append1"}
    assert append_result["results"][1] == {"key": "append2"}
    
    # 测试合并模式
    merge_node = IterativeWorkflowNode(
        # ...基本参数...
        result_collection_mode="merge",
        result_variable="merged_result",
        # ...其他参数...
    )
    merge_result = merge_node.execute({"input": "test"})
    assert merge_result["merged_result"] == {"key1": "merge1", "key2": "merge2"}  # 合并字典
```

## 总结

IterativeWorkflowNode 实现了以下关键功能：

1. **重复执行控制**
   - 基于自定义条件函数的迭代控制
   - 最大迭代次数限制保障
   - 迭代状态跟踪与管理

2. **数据传递机制**
   - 主工作流到迭代工作流的变量映射
   - 迭代间的变量传递和更新
   - 迭代结果回传到主工作流

3. **结果收集策略**
   - 替换模式：只保留最终结果
   - 追加模式：保留所有迭代结果
   - 合并模式：智能合并字典类型结果

4. **异常处理和安全机制**
   - 迭代条件错误处理
   - 最大迭代次数防护
   - 迭代状态追踪与日志

这种设计使IterativeWorkflowNode成为处理需要多轮改进、批量处理和渐进式任务的理想选择，显著增强了框架的功能和适用场景范围。