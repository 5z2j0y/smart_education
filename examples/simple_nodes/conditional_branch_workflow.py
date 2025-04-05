"""
条件分支工作流示例。
演示如何使用ConditionalBranchNode实现基于内容的动态分支。

----------------------------------------
示例输出：（输入：叽里咕噜劈里啪啦嗷嗷嗷）
----------------------------------------

--- 处理结果 ---
分类: Daily
置信度: 0.5
原因: The input consists of nonsensical or playful sounds, which are more likely to occur in casual daily conversation rather than in an educational context.
回答: 哈哈，看来你正在用一组超有趣的拟声词放飞自我呀！🤣 如果是想表达开心、烦躁、或者单纯想玩 声音游戏——我都准备好啦！需要帮忙翻译成“人类语”，还是想一起创作一首噼里啪啦交响诗？🎵 （悄悄说 ：嗷嗷嗷特别适合用来模仿小恐龙哦~ 🦖）
"""
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入所需组件
from src.workflow.base import WorkflowContext
from src.workflow.engine import Workflow
from src.workflow.nodes.start_node import StartNode
from src.workflow.nodes.llm_node import LLMNode
from src.workflow.nodes.end_node import EndNode
from src.workflow.nodes.conditional_branch_node import ConditionalBranchNode, ClassDefinition
from src.llm.deepseek_client import DeepSeekClient

def run_conditional_branch_workflow():
    """运行条件分支工作流示例"""
    
    # 获取 DeepSeek API 密钥
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误: DEEPSEEK_API_KEY 环境变量未设置")
        print("请设置环境变量后再运行，例如：")
        print("export DEEPSEEK_API_KEY='your-api-key-here'  # Linux/Mac")
        print("或")
        print("set DEEPSEEK_API_KEY=your-api-key-here  # Windows")
        return None
    
    # 创建 DeepSeek 客户端实例
    deepseek_llm = DeepSeekClient(api_key=api_key, model="deepseek-chat")
    print(f"已创建DeepSeek客户端，使用模型: {deepseek_llm.model}")

    # 定义流式输出的回调函数
    def stream_callback(text_chunk):
        """处理流式输出的文本片段"""
        print(text_chunk, end="", flush=True)

    # 定义分类
    classes = [
        ClassDefinition(
            name="Educational",
            description="教育相关的提问或陈述",
            next_node_id="educational_handler",
            examples=["什么是微积分?", "如何学好英语?"]
        ),
        ClassDefinition(
            name="Daily",
            description="日常生活对话",
            next_node_id="daily_handler",
            examples=["今天天气真好", "晚饭吃什么?"]
        )
    ]

    # 定义默认分类（兜底路由）
    default_class = ClassDefinition(
        name="General",
        description="无法明确分类的一般对话",
        next_node_id="general_handler"
    )

    # 定义节点
    start_node = StartNode(
        node_id="start", 
        node_name="Start", 
        output_variable_names=["user_query"],
        next_node_id="classifier"  # 设置StartNode的下一个节点
    )
    
    # 条件分支节点
    branch_node = ConditionalBranchNode(
        node_id="classifier",
        node_name="Query Classifier",
        classes=classes,
        input_variable_name="user_query",
        llm_client=deepseek_llm,
        default_class=default_class,
        output_reason=True
    )
    
    # 教育类处理节点
    educational_node = LLMNode(
        node_id="educational_handler",
        node_name="Educational Query Handler",
        system_prompt_template="这是一个教育相关问题。请详细解答: {user_query}",
        output_variable_name="response",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="educational_end"  # 指定下一个节点
    )
    
    # 日常类处理节点
    daily_node = LLMNode(
        node_id="daily_handler",
        node_name="Daily Query Handler",
        system_prompt_template="这是一个日常生活问题。请友好回答: {user_query}",
        output_variable_name="response",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="daily_end"  # 指定下一个节点
    )
    
    # 通用类处理节点
    general_node = LLMNode(
        node_id="general_handler",
        node_name="General Query Handler",
        system_prompt_template="请回答这个一般性问题: {user_query}",
        output_variable_name="response",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="general_end"  # 指定下一个节点
    )
    
    # 为每个分支创建独立的结束节点
    educational_end = EndNode(
        node_id="educational_end",
        node_name="Educational End",
        input_variable_names=["response"]
    )

    daily_end = EndNode(
        node_id="daily_end",
        node_name="Daily End",
        input_variable_names=["response"]
    )

    general_end = EndNode(
        node_id="general_end",
        node_name="General End",
        input_variable_names=["response"]
    )

    # 创建工作流实例
    workflow = Workflow([
        start_node,
        branch_node,
        educational_node,
        daily_node,
        general_node,
        educational_end,
        daily_end,
        general_end
    ])

    # 定义测试查询列表
    test_queries = [
        "叽里咕噜劈里啪啦嗷嗷嗷",
        "今天天气真好",
    ]

    for query in test_queries:
        print("\n" + "="*50)
        print(f"测试查询: {query}")
        print("="*50)
        
        # 设置初始上下文
        context = {"user_query": query}
        
        # 执行工作流
        try:
            final_context = workflow.run(context)
            
            # 输出结果
            print("\n--- 处理结果 ---")
            print(f"分类: {final_context['classification_result']['class_name']}")
            print(f"置信度: {final_context['classification_result'].get('confidence', 'N/A')}")
            if 'classification_result_reason' in final_context:
                print(f"原因: {final_context['classification_result_reason']}")
            print(f"回答: {final_context['response']}")
        except Exception as e:
            print(f"\n工作流执行失败: {e}")

    print("\n条件分支工作流执行完成！")
    return final_context  # 返回最后一个查询的最终上下文

if __name__ == "__main__":
    run_conditional_branch_workflow()
