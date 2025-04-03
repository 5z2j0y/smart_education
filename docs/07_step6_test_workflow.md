# 步骤6: 组装并测试示例工作流

本步骤我们将使用前面创建的所有组件，构建并测试一个完整的示例工作流。

## 任务

1. 创建 `FakeLLMClient` 实例
2. 创建工作流的各个节点：`StartNode`, `LLMNode`(两个), `EndNode`
3. 组装工作流并设置初始输入
4. 运行工作流并验证执行结果

## 代码实现

```python
# 导入所需组件
from base_node import WorkflowContext
from start_node import StartNode
from llm_node import LLMNode, FakeLLMClient
from end_node import EndNode
from workflow import Workflow

def run_example_workflow():
    """运行示例工作流的函数"""
    
    # 1. 创建 Fake LLM Client 实例
    fake_llm = FakeLLMClient()

    # 2. 定义节点
    # 开始节点 - 接收用户查询
    start_node = StartNode(
        node_id="start", 
        node_name="Start", 
        output_variable_names=["user_query"]
    )
    
    # 第一个LLM节点 - 优化用户查询
    llm_node_1 = LLMNode(
        node_id="llm1", 
        node_name="Better Query Generator",
        system_prompt_template="you need to better user's query. output with bettered user query without other words. here's your input: {user_query}",
        output_variable_name="better_query",
        llm_client=fake_llm
    )
    
    # 第二个LLM节点 - 回答优化后的查询
    llm_node_2 = LLMNode(
        node_id="llm2", 
        node_name="Query Answerer",
        system_prompt_template="you need to answer the query in detail. here's your input: {better_query}",
        output_variable_name="llm_answer",
        llm_client=fake_llm
    )
    
    # 结束节点 - 提取最终答案
    end_node = EndNode(
        node_id="end", 
        node_name="End", 
        input_variable_names=["llm_answer"]
    )

    # 3. 创建工作流
    workflow = Workflow(nodes=[start_node, llm_node_1, llm_node_2, end_node])

    # 4. 定义初始输入
    initial_input = {"user_query": "what is the youth?"}

    # 5. 运行工作流
    print("\n开始执行示例工作流...")
    final_context = workflow.run(initial_input)

    # 6. 检查结果
    print("\n=== 最终工作流上下文 ===")
    print(final_context)
    
    # 进行断言检查，确保工作流正确执行
    assert "user_query" in final_context, "缺少初始用户查询"
    assert "better_query" in final_context, "缺少优化后的查询"
    assert "llm_answer" in final_context, "缺少LLM回答"
    
    # 基于Fake LLM的预期响应进行检查
    assert final_context["better_query"] == "A detailed exploration of the concept of youth.", "优化后的查询不符合预期"
    assert final_context["llm_answer"] == "Youth is often defined as the period between childhood and adult age...", "LLM回答不符合预期"
    
    print("\n示例工作流执行成功！所有检查均已通过。")
    return final_context

# 执行示例工作流
if __name__ == "__main__":
    run_example_workflow()
```

## 期望的执行结果

执行上述代码后，应该看到类似下面的输出：

```
开始执行示例工作流...
=== Starting Workflow Execution ===
--- Executing StartNode(id='start', name='Start') ---
  Input Context: {'user_query': 'what is the youth?'}
  Output Context: {'user_query': 'what is the youth?'}
--- Finished StartNode(id='start', name='Start') ---

--- Executing LLMNode(id='llm1', name='Better Query Generator') ---
  Input Context: {'user_query': 'what is the youth?'}
  Formatted Prompt: you need to better user's query. output with bettered user query without other words. here's your input: what is the youth?
    [Fake LLM] Received prompt: you need to better user's query. output with bettered user query without other words. here's your i...
  LLM Response: A detailed exploration of the concept of youth.
  Output Context: {'user_query': 'what is the youth?', 'better_query': 'A detailed exploration of the concept of youth.'}
--- Finished LLMNode(id='llm1', name='Better Query Generator') ---

--- Executing LLMNode(id='llm2', name='Query Answerer') ---
  Input Context: {'user_query': 'what is the youth?', 'better_query': 'A detailed exploration of the concept of youth.'}
  Formatted Prompt: you need to answer the query in detail. here's your input: A detailed exploration of the concept of youth.
    [Fake LLM] Received prompt: you need to answer the query in detail. here's your input: A detailed exploration of the concept of...
  LLM Response: Youth is often defined as the period between childhood and adult age...
  Output Context: {'user_query': 'what is the youth?', 'better_query': 'A detailed exploration of the concept of youth.', 'llm_answer': 'Youth is often defined as the period between childhood and adult age...'}
--- Finished LLMNode(id='llm2', name='Query Answerer') ---

--- Executing EndNode(id='end', name='End') ---
  Input Context: {'user_query': 'what is the youth?', 'better_query': 'A detailed exploration of the concept of youth.', 'llm_answer': 'Youth is often defined as the period between childhood and adult age...'}
  Final Workflow Variables Extracted: {'llm_answer': 'Youth is often defined as the period between childhood and adult age...'}
  Output Context: {'user_query': 'what is the youth?', 'better_query': 'A detailed exploration of the concept of youth.', 'llm_answer': 'Youth is often defined as the period between childhood and adult age...'}
--- Finished EndNode(id='end', name='End') ---
=== Workflow Execution Finished Successfully ===

=== 最终工作流上下文 ===
{'user_query': 'what is the youth?', 'better_query': 'A detailed exploration of the concept of youth.', 'llm_answer': 'Youth is often defined as the period between childhood and adult age...'}

示例工作流执行成功！所有检查均已通过。
```

## 验证

执行上述代码后，确认：

1. 每个节点按预期顺序执行
2. 上下文正确在节点间传递和更新
3. 最终上下文包含所有预期的变量和值
4. 所有断言检查均成功通过

如果执行成功，表明基本工作流框架已经可以正常工作。下一步可以考虑集成真实的OpenAI客户端。
