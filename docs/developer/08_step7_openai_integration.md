# 步骤7: 集成OpenAI客户端（可选）

本步骤我们将用真实的`OpenAIClient`替换之前使用的`FakeLLMClient`，使工作流能够与实际的OpenAI API交互。

## 任务

1. 配置OpenAI API密钥
2. 创建 `OpenAIClient` 实例
3. 使用OpenAI客户端替换之前的假客户端
4. 运行工作流并验证真实API调用结果

## 代码实现

```python
# 导入所需组件
import os
from base_node import WorkflowContext
from start_node import StartNode
from llm_node import LLMNode, OpenAIClient
from end_node import EndNode
from workflow import Workflow

def run_openai_workflow():
    """使用OpenAI API运行工作流的函数"""
    
    # 1. 获取OpenAI API密钥
    # 安全起见，从环境变量获取API密钥，而不是硬编码
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("错误: 未设置OPENAI_API_KEY环境变量")
        print("请设置环境变量后再运行，例如：")
        print("export OPENAI_API_KEY='your-api-key-here'  # Linux/Mac")
        print("或")
        print("set OPENAI_API_KEY=your-api-key-here  # Windows")
        return None
    
    # 2. 创建 OpenAI Client 实例
    openai_client = OpenAIClient(api_key=api_key, model="gpt-3.5-turbo")
    print(f"已创建OpenAI客户端，使用模型: {openai_client.model}")

    # 3. 定义节点
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
        system_prompt_template="你需要改进用户的查询，使其更清晰、更有深度。只输出改进后的查询，不要有其他文字。用户查询是: {user_query}",
        output_variable_name="better_query",
        llm_client=openai_client
    )
    
    # 第二个LLM节点 - 回答优化后的查询
    llm_node_2 = LLMNode(
        node_id="llm2", 
        node_name="Query Answerer",
        system_prompt_template="请详细回答以下问题，提供丰富的内容和深入的解释: {better_query}",
        output_variable_name="llm_answer",
        llm_client=openai_client
    )
    
    # 结束节点 - 提取最终答案
    end_node = EndNode(
        node_id="end", 
        node_name="End", 
        input_variable_names=["llm_answer", "better_query", "user_query"]
    )

    # 4. 创建工作流
    workflow = Workflow(nodes=[start_node, llm_node_1, llm_node_2, end_node])

    # 5. 定义初始输入
    initial_input = {"user_query": "什么是人工智能？"}

    # 6. 运行工作流
    print("\n开始执行OpenAI工作流...")
    try:
        final_context = workflow.run(initial_input)
        
        # 7. 显示结果
        print("\n=== 工作流执行结果摘要 ===")
        print(f"原始查询: {final_context['user_query']}")
        print(f"优化查询: {final_context['better_query']}")
        print(f"最终回答: {final_context['llm_answer'][:200]}...")  # 只显示前200个字符
        
        print("\nOpenAI工作流执行成功！")
        return final_context
    except Exception as e:
        print(f"\n工作流执行失败: {e}")
        return None

# 执行OpenAI工作流
if __name__ == "__main__":
    run_openai_workflow()
```

## 安全注意事项

1. **API密钥管理**：
   - 永远不要在代码中硬编码API密钥
   - 使用环境变量或专门的密钥管理服务
   - 不要将包含API密钥的代码提交到版本控制系统

2. **成本控制**：
   - OpenAI API是收费服务，每次调用都会产生费用
   - 在开发测试阶段，可以：
     - 使用较小的模型（如gpt-3.5-turbo而非gpt-4）
     - 限制API调用频率
     - 设置API使用限额

## 故障排除

如果遇到API调用问题，请检查：

1. API密钥是否正确设置为环境变量
2. 网络连接是否正常
3. OpenAI服务是否可用（可查看OpenAI状态页面）
4. API请求是否超过了限额或速率限制

## 预期结果

执行成功后，将看到实际的OpenAI API响应，输出可能类似于：

```
已创建OpenAI客户端，使用模型: gpt-3.5-turbo

开始执行OpenAI工作流...
=== Starting Workflow Execution ===
--- Executing StartNode(id='start', name='Start') ---
  Input Context: {'user_query': '什么是人工智能？'}
  Output Context: {'user_query': '什么是人工智能？'}
--- Finished StartNode(id='start', name='Start') ---

--- Executing LLMNode(id='llm1', name='Better Query Generator') ---
  Input Context: {'user_query': '什么是人工智能？'}
  Formatted Prompt: 你需要改进用户的查询，使其更清晰、更有深度。只输出改进后的查询，不要有其他文字。用户查询是: 什么是人工智能？
  LLM Response: 人工智能的基本原理、发展历程、关键技术及其对社会经济和人类未来的深远影响是什么？
  Output Context: {'user_query': '什么是人工智能？', 'better_query': '人工智能的基本原理、发展历程、关键技术及其对社会经济和人类未来的深远影响是什么？'}
--- Finished LLMNode(id='llm1', name='Better Query Generator') ---

--- Executing LLMNode(id='llm2', name='Query Answerer') ---
  Input Context: {'user_query': '什么是人工智能？', 'better_query': '人工智能的基本原理、发展历程、关键技术及其对社会经济和人类未来的深远影响是什么？'}
  Formatted Prompt: 请详细回答以下问题，提供丰富的内容和深入的解释: 人工智能的基本原理、发展历程、关键技术及其对社会经济和人类未来的深远影响是什么？
  LLM Response: [详细的回答，可能非常长]
  Output Context: {'user_query': '什么是人工智能？', 'better_query': '人工智能的基本原理、发展历程、关键技术及其对社会经济和人类未来的深远影响是什么？', 'llm_answer': '[详细的回答]'}
--- Finished LLMNode(id='llm2', name='Query Answerer') ---

[以下内容省略]

=== 工作流执行结果摘要 ===
原始查询: 什么是人工智能？
优化查询: 人工智能的基本原理、发展历程、关键技术及其对社会经济和人类未来的深远影响是什么？
最终回答: [回答的前200个字符]...

OpenAI工作流执行成功！
```

实际输出将根据OpenAI模型的实时响应而变化。
