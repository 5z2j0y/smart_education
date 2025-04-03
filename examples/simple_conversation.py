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
from src.llm.deepseek_client import DeepSeekClient  # 替换为DeepSeekClient

def run_example_workflow():
    """运行示例工作流的函数"""
    
    # 1. 获取 DEEPSEEK API密钥
    # 安全起见，从环境变量获取API密钥，而不是硬编码
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误: DEEPSEEK_API_KEY 环境变量未设置")
        print("请设置环境变量后再运行，例如：")
        print("export DEEPSEEK_API_KEY='your-api-key-here'  # Linux/Mac")
        print("或")
        print("set DEEPSEEK_API_KEY=your-api-key-here  # Windows")
        return None
    
    # 创建 DeepSeek Client 实例
    deepseek_client = DeepSeekClient(api_key=api_key, model="deepseek-chat")
    print(f"已创建DeepSeek客户端，使用模型: {deepseek_client.model}")

    # 定义流式输出的回调函数
    def stream_callback(text_chunk):
        """处理流式输出的文本片段"""
        print(text_chunk, end="", flush=True)

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
        system_prompt_template="你需要改进用户的查询，使其更清晰、更有深度。只输出改进后的查询，不要有其他文字。用户查询是: {user_query}",
        output_variable_name="better_query",
        llm_client=deepseek_client,  # 使用DeepSeekClient
        stream=True,  # 启用流式输出
        stream_callback=stream_callback  # 自定义处理流式输出的回调
    )
    
    # 第二个LLM节点 - 回答优化后的查询
    llm_node_2 = LLMNode(
        node_id="llm2", 
        node_name="Query Answerer",
        system_prompt_template="请详细回答以下问题，提供丰富的内容和深入的解释: {better_query}",
        output_variable_name="llm_answer",
        llm_client=deepseek_client  # 使用DeepSeekClient
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
    initial_input = {"user_query": "什么是青春?"}

    # 5. 运行工作流
    print("\n开始执行OpenAI工作流...")
    try:
        final_context = workflow.run(initial_input)
        
        # 6. 显示结果
        print("\n=== 工作流执行结果摘要 ===")
        print(f"原始查询: {final_context.get('user_query')}")
        print(f"优化查询: {final_context.get('better_query')}")
        print("\n最终回答:")
        print(f"{final_context.get('llm_answer')}")  
        
        print("\nOpenAI工作流执行成功！")
        return final_context
    except Exception as e:
        print(f"\n工作流执行失败: {e}")
        return None

if __name__ == "__main__":
    run_example_workflow()
