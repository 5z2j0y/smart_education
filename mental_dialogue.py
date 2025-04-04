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
from src.workflow.nodes.conditional_branch_node import ConditionalBranchNode, ClassDefinition
from src.llm.deepseek_client import DeepSeekClient

def run_mental_dialogue_workflow():
    """运行心理对话工作流"""
    
    # 获取 DeepSeek API 密钥
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误: DEEPSEEK_API_KEY 环境变量未设置")
        return None
    
    # 创建 DeepSeek 客户端实例
    deepseek_llm = DeepSeekClient(api_key=api_key, model="deepseek-chat")

    # 定义分类
    classes = [
        ClassDefinition(
            name="Mental Health",
            description="用户心理健康相关问题",
            next_node_id="mental_health_handler",
            examples=["我最近很焦虑", "我感觉很抑郁"]
        ),
        ClassDefinition(
            name="Self-Harm Risk",
            description="用户有自我伤害风险",
            next_node_id="self_harm_handler",
            examples=["我不想活了", "我有自残的想法"]
        )
    ]

    # 定义默认分类（兜底路由）
    default_class = ClassDefinition(
        name="Daily Chat",
        description="日常聊天",
        next_node_id="daily_chat_handler"
    )

    # 定义节点
    start_node = StartNode(
        node_id="start", 
        node_name="Start Node", 
        output_variable_names=["user_query"],
        next_node_id="classifier"
    )
    
    branch_node = ConditionalBranchNode(
        node_id="classifier",
        node_name="Query Classifier",
        classes=classes,
        input_variable_name="user_query",
        llm_client=deepseek_llm,
        default_class=default_class,
        output_reason=True
    )
    
    mental_health_node = LLMNode(
        node_id="mental_health_handler",
        node_name="Mental Health Handler",
        system_prompt_template="用户提到心理健康问题，请提供支持性回答: {user_query}",
        output_variable_name="response",
        llm_client=deepseek_llm,
        stream=True,
        next_node_id="end_node"
    )
    
    self_harm_node = LLMNode(
        node_id="self_harm_handler",
        node_name="Self-Harm Risk Handler",
        system_prompt_template="用户可能有自我伤害风险，请提供紧急支持: {user_query}",
        output_variable_name="response",
        llm_client=deepseek_llm,
        stream=True,
        next_node_id="end_node"
    )
    
    daily_chat_node = LLMNode(
        node_id="daily_chat_handler",
        node_name="Daily Chat Handler",
        system_prompt_template="这是一个日常聊天，请友好回答: {user_query}",
        output_variable_name="response",
        llm_client=deepseek_llm,
        stream=True,
        next_node_id="end_node"
    )
    
    end_node = EndNode(
        node_id="end_node",
        node_name="End Node",
        input_variable_names=["response"]
    )

    # 创建工作流实例
    workflow = Workflow([
        start_node,
        branch_node,
        mental_health_node,
        self_harm_node,
        daily_chat_node,
        end_node
    ])

    # 测试查询
    test_queries = [
        "我最近很焦虑",
        "我不想活了",
        "今天天气真好"
    ]

    for query in test_queries:
        print("\n" + "="*50)
        print(f"测试查询: {query}")
        print("="*50)
        
        context = {"user_query": query}
        try:
            final_context = workflow.run(context)
            print("\n--- 处理结果 ---")
            print(f"分类: {final_context['classification_result']['class_name']}")
            print(f"回答: {final_context['response']}")
        except Exception as e:
            print(f"\n工作流执行失败: {e}")

    print("\n心理对话工作流执行完成！")

if __name__ == "__main__":
    run_mental_dialogue_workflow()
