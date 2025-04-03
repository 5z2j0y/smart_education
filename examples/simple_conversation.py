"""
简单对话工作流示例。
演示如何使用框架构建一个简单的两步对话工作流：
1. 优化用户查询
2. 回答优化后的查询
"""
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入所需组件
from src.workflow.base import WorkflowContext
from src.workflow.engine import Workflow
from src.workflow.nodes.start_node import StartNode
from src.workflow.nodes.llm_node import LLMNode
from src.workflow.nodes.end_node import EndNode
from src.llm.fake_client import FakeLLMClient

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

if __name__ == "__main__":
    run_example_workflow()
