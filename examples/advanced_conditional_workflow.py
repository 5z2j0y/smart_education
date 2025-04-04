"""
高级条件分支工作流示例。
演示如何使用多层条件分支和混合线性执行模式实现复杂交互。
"""
import sys
import os
import time

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

def run_advanced_conditional_workflow():
    """运行高级条件分支工作流示例"""
    
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
    
    # ====== 第一阶段：用户心情分类 ======
    
    # 定义心情分类
    mood_classes = [
        ClassDefinition(
            name="Positive",
            description="用户表达积极、高兴的情绪",
            next_node_id="positive_response",
            examples=["今天天气真好", "我很开心", "太棒了"]
        ),
        ClassDefinition(
            name="Negative",
            description="用户表达消极、不开心的情绪",
            next_node_id="negative_response",
            examples=["今天真糟糕", "我很难过", "太失望了"]
        )
    ]

    # 定义默认心情分类
    default_mood_class = ClassDefinition(
        name="Neutral",
        description="用户没有表达明显情绪或情绪不确定",
        next_node_id="neutral_response"
    )
    
    # ====== 第二阶段：回应评估分类 ======
    
    # 定义回应评估分类
    evaluation_classes = [
        ClassDefinition(
            name="Appropriate",
            description="AI回应得体，与用户情绪匹配，内容恰当",
            next_node_id="appropriate_end",
            examples=["回答很贴心", "理解了我的情绪", "回复很有帮助"]
        ),
        ClassDefinition(
            name="Inappropriate",
            description="AI回应不得体，与用户情绪不匹配，或内容不恰当",
            next_node_id="inappropriate_end",
            examples=["没理解我的意思", "回答跑题了", "情绪完全不对"]
        )
    ]
    
    # 定义默认评估分类
    default_evaluation_class = ClassDefinition(
        name="Neutral",
        description="无法确定AI回应的质量",
        next_node_id="neutral_evaluation_end"
    )
    
    # ====== 创建所有节点 ======
    
    # 开始节点
    start_node = StartNode(
        node_id="start", 
        node_name="Start Node", 
        output_variable_names=["user_input"]
        # 不指定next_node_id，使用线性顺序
    )
    
    # 心情分类节点
    mood_classifier = ConditionalBranchNode(
        node_id="mood_classifier",
        node_name="User Mood Classifier",
        classes=mood_classes,
        input_variable_name="user_input",
        llm_client=deepseek_llm,
        default_class=default_mood_class,
        output_reason=True
    )
    
    # 积极心情回应节点
    positive_response = LLMNode(
        node_id="positive_response",
        node_name="Positive Mood Response",
        system_prompt_template="用户看起来心情不错！请以积极愉快的语气回应：{user_input}",
        output_variable_name="ai_response",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="user_feedback"  # 显式指定下一个节点为用户反馈节点
    )
    
    # 消极心情回应节点
    negative_response = LLMNode(
        node_id="negative_response",
        node_name="Negative Mood Response",
        system_prompt_template="用户看起来心情不太好。请以温暖安慰的语气回应：{user_input}",
        output_variable_name="ai_response",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="user_feedback"  # 显式指定下一个节点为用户反馈节点
    )
    
    # 中性心情回应节点
    neutral_response = LLMNode(
        node_id="neutral_response",
        node_name="Neutral Mood Response",
        system_prompt_template="请以客观友好的语气回应用户的输入：{user_input}",
        output_variable_name="ai_response",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="user_feedback"  # 显式指定下一个节点为用户反馈节点
    )
    
    # 模拟用户反馈节点
    user_feedback = LLMNode(
        node_id="user_feedback",
        node_name="Simulated User Feedback",
        system_prompt_template="""
        请模拟用户对AI回复的一个简短回应。
        
        用户原始输入: {user_input}
        AI回复: {ai_response}
        
        作为用户，你会如何回应这个AI的回复？请给出一个简短的回应。
        """,
        output_variable_name="user_feedback",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback
        # 不指定next_node_id
    )
    
    # 回应评估节点
    response_evaluator = ConditionalBranchNode(
        node_id="response_evaluator",
        node_name="Response Quality Evaluator",
        classes=evaluation_classes,
        input_variable_name="user_feedback",
        llm_client=deepseek_llm,
        default_class=default_evaluation_class,
        output_reason=True
    )
    
    # 得体回应结束节点
    appropriate_end = EndNode(
        node_id="appropriate_end",
        node_name="Appropriate Response End",
        input_variable_names=["ai_response", "user_feedback", "classification_result", "classification_result_reason"]
    )
    
    # 不得体回应结束节点
    inappropriate_end = EndNode(
        node_id="inappropriate_end",
        node_name="Inappropriate Response End",
        input_variable_names=["ai_response", "user_feedback", "classification_result", "classification_result_reason"]
    )
    
    # 中性评估结束节点
    neutral_evaluation_end = EndNode(
        node_id="neutral_evaluation_end",
        node_name="Neutral Evaluation End",
        input_variable_names=["ai_response", "user_feedback", "classification_result", "classification_result_reason"]
    )
    
    # 按照线性顺序创建工作流
    # 注意：条件分支部分已经通过next_node_id显式指定，其他部分采用线性顺序
    workflow = Workflow([
        start_node,
        mood_classifier,
        positive_response,
        negative_response,
        neutral_response,
        user_feedback,
        response_evaluator,
        appropriate_end,
        inappropriate_end,
        neutral_evaluation_end
    ])
    
    # 定义测试输入列表
    test_inputs = [
        "今天天气真好，我很开心！",
        "最近工作压力很大，感觉很累。",
        "可以帮我分析一下这个问题吗？"
    ]
    
    # 执行工作流测试
    for user_input in test_inputs:
        print("\n" + "="*80)
        print(f"测试输入: {user_input}")
        print("="*80)
        
        # 设置初始上下文
        context = {"user_input": user_input}
        
        # 执行工作流
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 运行工作流
            final_context = workflow.run(context)
            
            # 计算运行时间
            execution_time = time.time() - start_time
            
            # 输出结果
            print("\n" + "-"*40)
            print("工作流执行结果:")
            print("-"*40)
            print(f"用户输入: {user_input}")
            print(f"心情分类: {final_context['classification_result']['class_name']}")
            print(f"AI回应: {final_context['ai_response']}")
            print(f"模拟用户反馈: {final_context['user_feedback']}")
            print(f"回应评估: {final_context.get('classification_result', {}).get('class_name')}")
            if 'classification_result_reason' in final_context:
                print(f"评估原因: {final_context['classification_result_reason']}")
            print(f"执行时间: {execution_time:.2f}秒")
        except Exception as e:
            print(f"\n工作流执行失败: {e}")
    
    print("\n高级条件分支工作流执行完成！")
    return final_context  # 返回最后一次执行的上下文

if __name__ == "__main__":
    run_advanced_conditional_workflow()
