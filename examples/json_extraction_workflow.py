"""
JSON提取工作流示例。
演示如何使用JSONExtractorNode从LLM输出中提取结构化数据。

----------------------------------------
示例输出：（输入：以下是您请求的用户信息:{"name": "张三","age": 28,"interests": ["编程", "阅读", "旅行"],"contact": {"email": "zhangsan@example.com","phone": "123-456-7890"}}）
----------------------------------------

提取的JSON数据:
姓名: 张三
年龄: 28
兴趣爱好: 编程, 阅读, 旅行
邮箱: zhangsan@example.com
电话: 123-456-7890
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
from src.workflow.nodes.json_extractor_node import JSONExtractorNode
from src.workflow.nodes.end_node import EndNode
from src.llm.fake_client import FakeLLMClient

def run_json_extraction_workflow():
    """运行JSON提取工作流示例"""
    
    # 创建 Fake LLM Client 实例（在实际应用中替换为真实的API客户端）
    fake_llm = FakeLLMClient()
    
    # 自定义FakeLLMClient的响应，使其返回JSON
    original_invoke = fake_llm.invoke
    def custom_invoke(prompt):
        if "JSON格式返回" in prompt:
            return """以下是您请求的用户信息:
            {
                "name": "张三",
                "age": 28,
                "interests": ["编程", "阅读", "旅行"],
                "contact": {
                    "email": "zhangsan@example.com",
                    "phone": "123-456-7890"
                }
            }
            希望这些信息对您有所帮助！"""
        return original_invoke(prompt)
    
    fake_llm.invoke = custom_invoke

    # 定义JSON模式
    user_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"},
            "interests": {"type": "array", "items": {"type": "string"}},
            "contact": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "phone": {"type": "string"}
                }
            }
        },
        "required": ["name", "age"]
    }

    # 定义节点
    start_node = StartNode(
        node_id="start", 
        node_name="Start", 
        output_variable_names=["query"]
    )
    
    llm_node = LLMNode(
        node_id="llm", 
        node_name="JSON Generator",
        system_prompt_template="请以JSON格式返回以下查询的结果: {query}",
        output_variable_name="llm_response",
        llm_client=fake_llm
    )
    
    json_extractor = JSONExtractorNode(
        node_id="json_extract",
        node_name="JSON Extractor",
        input_variable_name="llm_response",
        output_variable_name="user_data",
        schema=user_schema,  # 使用模式验证
        default_value={"status": "error", "message": "Failed to extract JSON"},
        raise_on_error=False  # 出错时使用默认值而不是抛出异常
    )
    
    end_node = EndNode(
        node_id="end", 
        node_name="End", 
        input_variable_names=["user_data"]
    )

    # 创建工作流
    workflow = Workflow([start_node, llm_node, json_extractor, end_node])

    # 定义初始输入
    initial_input = {"query": "获取用户张三的完整信息"}

    # 运行工作流
    print("\n开始执行JSON提取工作流...")
    final_context = workflow.run(initial_input)

    # 输出结果
    print("\n=== JSON提取工作流结果 ===")
    print(f"原始查询: {final_context['query']}")
    print(f"LLM响应: {final_context['llm_response']}")
    print("\n提取的JSON数据:")
    
    user_data = final_context['user_data']
    print(f"姓名: {user_data.get('name')}")
    print(f"年龄: {user_data.get('age')}")
    print(f"兴趣爱好: {', '.join(user_data.get('interests', []))}")
    if 'contact' in user_data:
        print(f"邮箱: {user_data['contact'].get('email')}")
        print(f"电话: {user_data['contact'].get('phone')}")
    
    print("\nJSON提取工作流执行完成！")
    return final_context

if __name__ == "__main__":
    run_json_extraction_workflow()
