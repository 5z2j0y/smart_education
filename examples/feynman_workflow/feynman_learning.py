"""
费曼学习工作流实现

这个脚本实现了费曼学习法工作流，通过以下步骤帮助用户深入理解知识：
1. 用户提供初始回答
2. 系统评估回答的准确性和完整性
3. 根据评估结果，引导用户修正严重错误或改进轻微瑕疵
4. 迭代改进直到达到满意的理解水平

使用方法：
python feynman_learning.py "你想要解释的主题的初始回答"
"""

import sys
import os
import time
from colorama import Fore, Style, init

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入所需组件
from src.workflow.base import WorkflowContext
from src.workflow.engine import Workflow
from src.workflow.nodes.start_node import StartNode
from src.workflow.nodes.input_node import InputNode
from src.workflow.nodes.llm_node import LLMNode
from src.workflow.nodes.conditional_branch_node import ConditionalBranchNode, ClassDefinition
from src.workflow.nodes.subworkflow_node import SubWorkflowNode
from src.workflow.nodes.end_node import EndNode
from src.llm.deepseek_client import DeepSeekClient

# 初始化colorama
init(autoreset=True)

def create_feynman_workflow(llm_client):
    """
    创建费曼学习法工作流
    
    Args:
        llm_client: LLM客户端实例
        
    Returns:
        Workflow: 配置好的费曼工作流实例
    """
    
    # 定义流式输出的回调函数
    def stream_callback(text_chunk):
        """处理流式输出的文本片段"""
        print(text_chunk, end="", flush=True)
    
    # ====== 主工作流节点 ======
    
    # 开始节点
    start_node = StartNode(
        node_id="start",
        node_name="开始节点",
        output_variable_names=["answer"],
        next_node_id="llm_node"
    )
    
    # 用户输入节点 - 主要用于后续迭代
    input_node = InputNode(
        node_id="input_node",
        node_name="用户输入节点",
        prompt_text="请根据反馈修改您的回答：",
        output_variable_name="answer",
        next_node_id="llm_node"
    )
    
    # 逻辑评估节点
    llm_node = LLMNode(
        node_id="llm_node",
        node_name="逻辑评估节点",
        system_prompt_template="""
        你是费曼工作流中的评估节点，请根据用户的陈述 {answer}，
        评估其是否合理，或者是否存在偏颇。你首先理解用户的陈述，
        然后如果有显著错误，明确纠正用户；如果有偏微瑕疵，友善地提醒用户。
        """,
        output_variable_name="evaluate_text",
        llm_client=llm_client,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="condition_branch"
    )
    
    # 条件分支节点
    classes = [
        ClassDefinition(
            name="major_defect",
            description="经过评估，用户的陈述 (answer) 具有重大错误。需要严格纠正。",
            next_node_id="major_defect_handler",
            examples=["完全错误", "概念混淆", "重大误解"]
        ),
        ClassDefinition(
            name="minor_defect",
            description="经过评估，用户的陈述 (answer) 具有轻微瑕疵，或者没有错误。需要友善地提醒。",
            next_node_id="minor_defect_handler",
            examples=["基本正确", "小错误", "可以改进"]
        )
    ]
    
    default_class = ClassDefinition(
        name="neutral",
        description="未分类的情况，默认处理。",
        next_node_id="neutral_handler"
    )
    
    condition_branch = ConditionalBranchNode(
        node_id="condition_branch",
        node_name="条件分支节点",
        classes=classes,
        input_variable_name="evaluate_text",
        llm_client=llm_client,
        default_class=default_class,
        output_reason=True
    )
    
    # ====== 重大错误处理子工作流 ======
    
    # 文本改进节点
    improvement_node = LLMNode(
        node_id="improvement_node",
        node_name="文本改进节点",
        system_prompt_template="""
        你是费曼工作流中的改进节点，请根据改进的建议 {evaluate_text} 引导用户更新自己的陈述 {answer}。
        提供清晰的指导，帮助用户理解其错误并改进。
        """,
        output_variable_name="updated_answer",
        llm_client=llm_client,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="return_to_input"
    )
    
    # 返回用户输入节点
    return_to_input = InputNode(
        node_id="return_to_input",
        node_name="返回用户输入节点",
        prompt_text="请根据改进建议更新您的陈述：",
        output_variable_name="updated_answer",
        next_node_id="end_subworkflow"
    )
    
    # 子工作流结束节点
    end_major_subworkflow = EndNode(
        node_id="end_subworkflow",
        node_name="子工作流结束节点",
        input_variable_names=["updated_answer"]
    )
    
    # 创建重大错误处理子工作流
    major_defect_handler = SubWorkflowNode(
        node_id="major_defect_handler",
        node_name="重大错误处理子工作流",
        nodes=[improvement_node, return_to_input, end_major_subworkflow],
        input_mapping={"evaluate_text": "evaluate_text", "answer": "answer"},
        output_mapping={"updated_answer": "updated_answer"},
        entry_node_id="improvement_node",
        exit_node_id="end_subworkflow",
        next_node_id="input_node"  # 返回主工作流继续迭代
    )
    
    # ====== 轻微瑕疵处理子工作流 ======
    
    # 改进引导节点
    improvement_guidance = LLMNode(
        node_id="improvement_guidance",
        node_name="改进引导节点",
        system_prompt_template="""
        你是费曼工作流中的改进节点，用户的回答 {answer} 已经相对正确答案。
        请根据评估节点的反馈 {evaluate_text} 进一步引导用户完善自己的陈述。
        提供友善的建议，帮助用户更深入地理解主题。
        """,
        output_variable_name="updated_answer",
        llm_client=llm_client,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="minor_user_input"
    )
    
    # 用户输入节点
    minor_user_input = InputNode(
        node_id="minor_user_input",
        node_name="用户输入节点",
        prompt_text="请根据改进建议更新您的陈述：",
        output_variable_name="updated_answer",
        next_node_id="summary_node"
    )
    
    # 总结节点
    summary_node = LLMNode(
        node_id="summary_node",
        node_name="总结节点",
        system_prompt_template="""
        你是费曼工作流中的总结节点，用户的回答 {updated_answer} 已经很好。
        请根据本次工作流的对话，帮助用户总结关键知识点和学到的知识。
        基于原始回答 {answer} 和评估反馈 {evaluate_text}，
        提供深入而有见解的总结，强化用户的理解。
        """,
        output_variable_name="summary",
        llm_client=llm_client,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="end_minor_subworkflow"
    )
    
    # 子工作流结束节点
    end_minor_subworkflow = EndNode(
        node_id="end_minor_subworkflow",
        node_name="子工作流结束节点",
        input_variable_names=["updated_answer", "summary"]
    )
    
    # 创建轻微瑕疵处理子工作流
    minor_defect_handler = SubWorkflowNode(
        node_id="minor_defect_handler",
        node_name="轻微瑕疵处理子工作流",
        nodes=[improvement_guidance, minor_user_input, summary_node, end_minor_subworkflow],
        input_mapping={"evaluate_text": "evaluate_text", "answer": "answer"},
        output_mapping={"updated_answer": "updated_answer", "summary": "summary"},
        entry_node_id="improvement_guidance",
        exit_node_id="end_minor_subworkflow",
        next_node_id="end_node"  # 完成工作流
    )
    
    # 默认处理节点
    neutral_handler = EndNode(
        node_id="neutral_handler",
        node_name="默认处理节点",
        input_variable_names=["evaluate_text", "updated_answer"]
    )
    
    # 主工作流结束节点
    end_node = EndNode(
        node_id="end_node",
        node_name="结束节点",
        input_variable_names=["evaluate_text", "updated_answer", "summary"]
    )
    
    # 创建完整工作流
    workflow = Workflow([
        start_node,
        input_node,
        llm_node,
        condition_branch,
        major_defect_handler,
        minor_defect_handler,
        neutral_handler,
        end_node
    ])
    
    return workflow

def run_feynman_workflow(initial_answer):
    """
    运行费曼学习工作流
    
    Args:
        initial_answer: 用户的初始回答
        
    Returns:
        WorkflowContext: 工作流执行后的最终上下文
    """
    # 获取 DeepSeek API 密钥
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print(f"{Fore.RED}错误: DEEPSEEK_API_KEY 环境变量未设置{Style.RESET_ALL}")
        print("请设置环境变量后再运行，例如：")
        print("export DEEPSEEK_API_KEY='your-api-key-here'  # Linux/Mac")
        print("或")
        print("set DEEPSEEK_API_KEY=your-api-key-here  # Windows")
        return None
    
    # 创建 DeepSeek 客户端实例
    deepseek_llm = DeepSeekClient(api_key=api_key, model="deepseek-chat")
    print(f"{Fore.GREEN}已创建DeepSeek客户端，使用模型: {deepseek_llm.model}{Style.RESET_ALL}")
    
    # 创建费曼工作流
    workflow = create_feynman_workflow(deepseek_llm)
    
    # 设置初始上下文
    context = {"answer": initial_answer}
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 运行工作流
        print(f"\n{Fore.CYAN}=== 费曼学习工作流开始 ==={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}初始回答:{Style.RESET_ALL}")
        print(f"{initial_answer}\n")
        print(f"{Fore.CYAN}正在评估您的回答...{Style.RESET_ALL}\n")
        
        final_context = workflow.run(context)
        
        # 计算运行时间
        execution_time = time.time() - start_time
        
        # 打印结果摘要
        print(f"\n{Fore.CYAN}=== 费曼学习工作流完成 ==={Style.RESET_ALL}")
        print(f"{Fore.GREEN}执行时间:{Style.RESET_ALL} {execution_time:.2f}秒")
        
        # 如果有总结，显示总结
        if "summary" in final_context and final_context["summary"]:
            print(f"\n{Fore.GREEN}学习总结:{Style.RESET_ALL}")
            print(final_context["summary"])
        
        # 显示最终改进的回答
        if "updated_answer" in final_context and final_context["updated_answer"]:
            print(f"\n{Fore.GREEN}最终改进的回答:{Style.RESET_ALL}")
            print(final_context["updated_answer"])
        
        return final_context
        
    except Exception as e:
        print(f"\n{Fore.RED}工作流执行失败: {e}{Style.RESET_ALL}")
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    # 从命令行参数获取初始回答，或使用默认示例
    if len(sys.argv) > 1:
        initial_answer = sys.argv[1]
    else:
        # initial_answer = "地球为什么是圆的？因为地球是一个球，而不是一个平面。"
        initial_answer = "晚上看到白白的月亮是因为月亮会发光，而不是太阳的反射"
        print(f"{Fore.YELLOW}未提供初始回答，使用示例：{initial_answer}{Style.RESET_ALL}")
    
    # 运行费曼工作流
    run_feynman_workflow(initial_answer)
