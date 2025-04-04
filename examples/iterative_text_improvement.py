"""
迭代文本改进示例。
演示如何使用迭代工作流节点逐步改进文本质量，直到达到预期标准。
"""
import sys
import os
import json
import time
from colorama import Fore, Style, init

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入所需组件
from src.workflow.base import WorkflowContext
from src.workflow.engine import Workflow
from src.workflow.nodes.start_node import StartNode
from src.workflow.nodes.llm_node import LLMNode
from src.workflow.nodes.end_node import EndNode
from src.workflow.nodes.iterative_workflow_node import IterativeWorkflowNode
from src.llm.deepseek_client import DeepSeekClient
from src.workflow.nodes.json_extractor_node import JSONExtractorNode

# 初始化colorama
init(autoreset=True)

def run_iterative_improvement_workflow():
    """运行迭代文本改进工作流示例"""
    
    # 初始化返回值
    final_context = None
    
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
    
    # 定义迭代条件函数
    def quality_check(context):
        """根据文本质量评分决定是否继续迭代"""
        if "evaluation" not in context:
            return True  # 首次迭代，还没有评估结果
        
        try:
            # 获取评估结果
            eval_data = context["evaluation"]
            # 如果是字符串则解析，否则直接使用
            if isinstance(eval_data, str):
                eval_data = json.loads(eval_data)
            
            quality_score = eval_data.get("quality_score", 0)
            iteration_count = context.get("_iteration_count", 0)
            
            # 打印当前质量分数
            print(f"\n{Fore.CYAN}当前质量分数: {quality_score:.2f}{Style.RESET_ALL}")
            
            # 如果质量分数低于0.8，继续迭代
            return quality_score < 0.8
        except Exception as e:
            print(f"评估结果解析错误: {e}")
            return False  # 出错时停止迭代
    
    # ====== 创建迭代工作流的节点 ======
    
    # 子工作流的开始节点
    draft_start = StartNode(
        node_id="draft_start",
        node_name="Draft Start",
        output_variable_names=["text_draft"]
    )
    
    # 文本改进节点
    improve_text = LLMNode(
        node_id="improve_text",
        node_name="Text Improvement",
        system_prompt_template="""
        你是一位专业的文本编辑，负责改进以下文本，使其更清晰、更专业、更有吸引力。
        请确保保留原始含义，同时提升表达质量。
        
        待改进文本:
        {text_draft}
        
        请直接给出改进后的文本，不要包含解释或其他内容。
        """,
        output_variable_name="improved_text",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback
    )
    
    # 质量评估节点
    evaluate_text = LLMNode(
        node_id="evaluate_text",
        node_name="Quality Evaluation",
        system_prompt_template="""
        请评估以下文本的质量，并返回一个包含以下内容的JSON对象:
        1. quality_score：0.0到1.0之间的分数，表示文本质量
        2. feedback：改进建议
        3. strengths：文本的优点
        4. weaknesses：文本的不足
        
        待评估文本:
        {improved_text}
        
        请确保返回有效的JSON格式，例如:
        {{"quality_score": 0.75, "feedback": "详细的改进建议...", "strengths": "优点...", "weaknesses": "不足..."}}
        """,
        output_variable_name="evaluation_text",
        llm_client=deepseek_llm
    )
    
    # JSON 提取节点
    extract_evaluation = JSONExtractorNode(
        node_id="extract_evaluation",
        node_name="Extract Evaluation JSON",
        input_variable_name="evaluation_text",
        output_variable_name="evaluation",
        default_value={"quality_score": 0.5, "feedback": "无法提取有效评估"},
        raise_on_error=False
    )
    
    # 创建迭代工作流节点
    text_improver = IterativeWorkflowNode(
        node_id="text_improver",
        node_name="Iterative Text Improvement",
        nodes=[draft_start, improve_text, evaluate_text, extract_evaluation],
        condition_function=quality_check,
        max_iterations=3,
        input_mapping={"initial_draft": "text_draft"},
        iteration_mapping={
        "improved_text": "text_draft",
        "evaluation": "evaluation"  # 确保评估结果在迭代间保留
    },
        output_mapping={
            "improved_text": "final_text", 
            "evaluation": "final_evaluation"
        },
        result_collection_mode="append",
        result_variable="improvement_history",
        next_node_id="summary_node"
    )
    
    # 主工作流的开始节点
    start_node = StartNode(
        node_id="start",
        node_name="Start Node",
        output_variable_names=["initial_draft"]
    )
    
    # 改进总结节点
    summary_node = LLMNode(
        node_id="summary_node",
        node_name="Improvement Summary",
        system_prompt_template="""
        请总结文本改进的过程，分析改进前后的对比。
        
        原始文本:
        {initial_draft}
        
        最终文本:
        {final_text}
        
        最终评估:
        {final_evaluation}
        
        请给出简要的改进分析和总结。
        """,
        output_variable_name="improvement_summary",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback
    )
    
    # 结束节点
    end_node = EndNode(
        node_id="end",
        node_name="End Node",
        input_variable_names=[
            "initial_draft",
            "final_text", 
            "final_evaluation",
            "improvement_summary", 
            "improvement_history",
            "_iterations_completed"
        ]
    )
    
    # 创建主工作流
    workflow = Workflow([
        start_node,
        text_improver,
        summary_node,
        end_node
    ])
    
    # 测试样例文本
    sample_texts = [
        "地球为什么是圆的？因为地球是一个球，而不是一个方"
    ]
    
    # 执行工作流
    for text in sample_texts:
        print("\n" + "="*80)
        print(f"{Fore.GREEN}原始文本:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{text}{Style.RESET_ALL}")
        print("="*80 + "\n")
        
        # 设置初始上下文
        context = {"initial_draft": text}
        final_context = None  # 初始化为 None
        
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 运行工作流
            final_context = workflow.run(context)
            
            # 计算运行时间
            execution_time = time.time() - start_time
            
            # 打印结果
            print("\n" + "-"*40)
            print(f"{Fore.GREEN}改进过程摘要:{Style.RESET_ALL}")
            print("-"*40)
            print(f"{Fore.GREEN}迭代次数:{Style.RESET_ALL} {final_context['_iterations_completed']}")
            print(f"{Fore.GREEN}执行时间:{Style.RESET_ALL} {execution_time:.2f}秒")
            
            # 打印改进历史
            if "improvement_history" in final_context and final_context["improvement_history"]:
                print(f"\n{Fore.GREEN}改进历史:{Style.RESET_ALL}")
                for i, version in enumerate(final_context["improvement_history"]):
                    print(f"\n{Fore.CYAN}版本 {i+1}:{Style.RESET_ALL}")
                    print(version)
            
        except Exception as e:
            print(f"\n{Fore.RED}工作流执行失败: {e}{Style.RESET_ALL}")
            import traceback
            print(traceback.format_exc())
    
    print(f"\n{Fore.GREEN}迭代改进工作流演示执行完成！{Style.RESET_ALL}")
    return final_context  # 现在即使出错也能返回 None

if __name__ == "__main__":
    run_iterative_improvement_workflow()
