"""
子工作流节点演示。
展示如何使用SubWorkflowNode封装复杂逻辑，提高代码模块化和可维护性。

----------------------------------------
示例输出：（输入："今天天气真好，我很开心！"）
----------------------------------------

用户输入: 今天天气真好，我很开心！
心情分类: Positive
AI回应: 哇～真的呢！阳光像蜂蜜一样甜甜的洒在身上，连风都在跳圆舞曲🌞 看到您这么开心，感觉世界都冒起了彩虹泡泡！要不要和我分享下今天的美好小事呀？是遇见了会微笑的云朵，还是收到了春天偷偷送的 芬芳呀～ (*^▽^*)
模拟用户反馈: "哈哈你描述得好有画面感呀～其实是因为上班路上看到樱花开了，粉粉的一片超治愈！突然就觉得今天特别幸运呢🌸"
回应评估: Appropriate
评估原因: 用户表达了对AI描述的赞赏，并分享了个人愉悦的经历和情绪，整体氛围积极且匹配。
执行时间: 36.44秒
"""

import sys
import os
import time
from colorama import Fore, Style, init

# 初始化colorama
init()

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入所需组件
from src.workflow.base import WorkflowContext
from src.workflow.engine import Workflow
from src.workflow.nodes.start_node import StartNode
from src.workflow.nodes.llm_node import LLMNode
from src.workflow.nodes.end_node import EndNode
from src.workflow.nodes.conditional_branch_node import ConditionalBranchNode, ClassDefinition
from src.workflow.nodes.subworkflow_node import SubWorkflowNode
from src.llm.deepseek_client import DeepSeekClient

def run_subworkflow_demo():
    """使用子工作流节点来封装高级条件分支工作流"""
    
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
    
    # ====== 第一阶段：用户心情分类及响应 - 子工作流 ======
    
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
    
    # 心情分类节点
    mood_classifier = ConditionalBranchNode(
        node_id="mood_classifier",
        node_name="User Mood Classifier",
        classes=mood_classes,
        input_variable_name="user_query",  # 子工作流内使用的变量名
        llm_client=deepseek_llm,
        default_class=default_mood_class,
        output_reason=True
    )
    
    # 积极心情回应节点
    positive_response = LLMNode(
        node_id="positive_response",
        node_name="Positive Mood Response",
        system_prompt_template="用户看起来心情不错！请以积极愉快的语气回应：{user_query}",
        output_variable_name="response",  # 子工作流内的输出变量名
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback
    )
    
    # 消极心情回应节点
    negative_response = LLMNode(
        node_id="negative_response",
        node_name="Negative Mood Response",
        system_prompt_template="用户看起来心情不太好。请以温暖安慰的语气回应：{user_query}",
        output_variable_name="response",  # 子工作流内的输出变量名
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback
    )
    
    # 中性心情回应节点
    neutral_response = LLMNode(
        node_id="neutral_response",
        node_name="Neutral Mood Response",
        system_prompt_template="请以客观友好的语气回应用户的输入：{user_query}",
        output_variable_name="response",  # 子工作流内的输出变量名
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback
    )
    
    # 心情分类和响应子工作流
    mood_response_subworkflow = SubWorkflowNode(
        node_id="mood_response_workflow",
        node_name="Mood Classification and Response Workflow",
        nodes=[mood_classifier, positive_response, negative_response, neutral_response],
        input_mapping={"user_input": "user_query"},  # 将主工作流的user_input映射到子工作流的user_query
        output_mapping={
            "response": "ai_response",  # 将子工作流的response映射到主工作流的ai_response
            "classification_result": "mood_classification",  # 保存心情分类结果
            "classification_result_reason": "mood_classification_reason"  # 保存心情分类原因
        },
        entry_node_id="mood_classifier"  # 从心情分类节点开始执行
    )
    
    # ====== 第二阶段：模拟用户反馈节点（不在子工作流内）======
    
    # 模拟用户反馈节点
    user_feedback = LLMNode(
        node_id="user_feedback",
        node_name="Simulated User Feedback",
        system_prompt_template="""
        请模拟用户对AI回复的一个简短回应。
        
        用户原始输入: {user_input}
        AI回复: {ai_response}
        
        作为用户，你会如何回应这个AI的回复？请给出一个简短的回应。不需要解释或理由。
        """,
        output_variable_name="user_feedback",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback
    )
    
    # ====== 第三阶段：回应评估子工作流 ======
    
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
    
    # 回应评估节点
    response_evaluator = ConditionalBranchNode(
        node_id="response_evaluator",
        node_name="Response Quality Evaluator",
        classes=evaluation_classes,
        input_variable_name="feedback",  # 子工作流内使用的变量名
        llm_client=deepseek_llm,
        default_class=default_evaluation_class,
        output_reason=True
    )
    
    # 得体回应结束节点
    appropriate_end = EndNode(
        node_id="appropriate_end",
        node_name="Appropriate Response End",
        input_variable_names=["feedback", "ai_response_copy", "classification_result", "classification_result_reason"]
    )
    
    # 不得体回应结束节点
    inappropriate_end = EndNode(
        node_id="inappropriate_end",
        node_name="Inappropriate Response End",
        input_variable_names=["feedback", "ai_response_copy", "classification_result", "classification_result_reason"]
    )
    
    # 中性评估结束节点
    neutral_evaluation_end = EndNode(
        node_id="neutral_evaluation_end",
        node_name="Neutral Evaluation End",
        input_variable_names=["feedback", "ai_response_copy", "classification_result", "classification_result_reason"]
    )
    
    # 回应评估子工作流
    response_evaluation_subworkflow = SubWorkflowNode(
        node_id="response_evaluation_workflow",
        node_name="Response Evaluation Workflow",
        nodes=[response_evaluator, appropriate_end, inappropriate_end, neutral_evaluation_end],
        input_mapping={
            "user_feedback": "feedback",  # 将主工作流的user_feedback映射到子工作流的feedback
            "ai_response": "ai_response_copy"  # 将主工作流的ai_response传递给子工作流
        },
        output_mapping={
            "classification_result": "evaluation_result",  # 将子工作流的分类结果映射到主工作流
            "classification_result_reason": "evaluation_reason"  # 将子工作流的分类原因映射到主工作流
        },
        entry_node_id="response_evaluator"  # 从评估节点开始执行
    )
    
    # 主工作流的开始节点
    start_node = StartNode(
        node_id="start", 
        node_name="Start Node", 
        output_variable_names=["user_input"]
    )
    
    # 主工作流的结束节点
    end_node = EndNode(
        node_id="end",
        node_name="Main Workflow End",
        input_variable_names=[
            "user_input", "ai_response", "user_feedback", 
            "mood_classification", "mood_classification_reason",
            "evaluation_result", "evaluation_reason"
        ]
    )
    
    # 创建主工作流
    workflow = Workflow([
        start_node,
        mood_response_subworkflow,  # 第一个子工作流
        user_feedback,             # 模拟用户反馈节点
        response_evaluation_subworkflow,  # 第二个子工作流
        end_node                   # 主工作流结束节点
    ])
    
    # 定义测试输入列表
    test_inputs = [
        "今天是清明节假期，天气也很好。"
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
            print(f"{Fore.GREEN}用户输入:{Style.RESET_ALL} {user_input}")
            print(f"{Fore.GREEN}心情分类:{Style.RESET_ALL} {final_context['mood_classification']['class_name']}")
            print(f"{Fore.GREEN}AI回应:{Style.RESET_ALL} {final_context['ai_response']}")
            print(f"{Fore.GREEN}模拟用户反馈:{Style.RESET_ALL} {final_context['user_feedback']}")
            print(f"{Fore.GREEN}回应评估:{Style.RESET_ALL} {final_context['evaluation_result']['class_name']}")
            print(f"{Fore.GREEN}评估原因:{Style.RESET_ALL} {final_context['evaluation_reason']}")
            print(f"{Fore.GREEN}执行时间:{Style.RESET_ALL} {execution_time:.2f}秒")
        except Exception as e:
            print(f"\n{Fore.RED}工作流执行失败: {e}{Style.RESET_ALL}")
            import traceback
            print(traceback.format_exc())
    
    print(f"\n{Fore.GREEN}子工作流演示执行完成！{Style.RESET_ALL}")
    return final_context  # 返回最后一次执行的上下文

if __name__ == "__main__":
    run_subworkflow_demo()
