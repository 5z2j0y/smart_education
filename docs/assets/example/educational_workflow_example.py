"""
教育工作流示例。
根据design.html文件中的设计实现教育领域工作流，
展示如何处理简单和复杂的学习问题。
"""

import sys
import os
import time
from colorama import Fore, Style, init

# 初始化colorama
init()

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

def run_educational_workflow():
    """基于设计文档实现教育工作流"""
    
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
    
    # 定义问题类型分类
    question_types = [
        ClassDefinition(
            name="复杂问题",
            description="这是一个复杂学习问题，需要深入分析",
            next_node_id="complex_query_optimizer",
            examples=["请分析成吉思汗的历史贡献及其影响。", "解释工业革命对现代社会的深远影响。"]
        ),
        ClassDefinition(
            name="简单问题",
            description="这是一个日常简单问题，可以直接回答",
            next_node_id="simple_query_handler",
            examples=["成吉思汗是谁？", "工业革命是什么时候发生的？"]
        )
    ]
    
    # 定义主工作流的节点
    
    # 开始节点
    start_node = StartNode(
        node_id="start", 
        node_name="Start Node", 
        output_variable_names=["User_query", "Subject", "Syllabus"]
    )
    
    # 问题类型分支节点
    branch_node = ConditionalBranchNode(
        node_id="branch",
        node_name="Question Type Classifier",
        classes=question_types,
        input_variable_name="User_query",
        llm_client=deepseek_llm,
        output_reason=True
    )
    
    # 复杂问题优化器节点
    complex_query_optimizer = LLMNode(
        node_id="complex_query_optimizer",
        node_name="复杂问题优化器",
        system_prompt_template="你是一个{Subject}学科助教，请根据课程标准{Syllabus}，分析学生意图，联想相关知识点，优化学生的提问：{User_query}",
        output_variable_name="Bettered_query",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="complex_query_answer"
    )
    
    # 复杂问题回答节点
    complex_query_answer = LLMNode(
        node_id="complex_query_answer",
        node_name="复杂问题回答",
        system_prompt_template="你是一个{Subject}学科教授，请根据详细回答学生提出的、经过助教优化后的提问和课程设计方案：{Bettered_query}，给出详细的回答：{User_query}",
        output_variable_name="final_answer",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="end"
    )
    
    # 简单问题回答节点
    simple_query_handler = LLMNode(
        node_id="simple_query_handler",
        node_name="简单问题回答",
        system_prompt_template="你是一个{Subject}学科助教，请根据课程标准{Syllabus}，简要回答学生的日常问题：{User_query}",
        output_variable_name="final_answer",
        llm_client=deepseek_llm,
        stream=True,
        stream_callback=stream_callback,
        next_node_id="end"
    )
    
    # 结束节点
    end_node = EndNode(
        node_id="end",
        node_name="End Node",
        input_variable_names=["User_query", "final_answer"]
    )
    
    # 创建工作流
    workflow = Workflow([
        start_node,
        branch_node,
        complex_query_optimizer,
        complex_query_answer,
        simple_query_handler,
        end_node
    ])
    
    # 定义测试输入
    test_inputs = [
        {
            "User_query": "成吉思汗是谁？",
            "Subject": "历史",
            "Syllabus": "普通高中历史课程标准（2017年版2022年修订）"
        },
        {
            "User_query": "请分析成吉思汗的历史贡献及其影响。",
            "Subject": "历史",
            "Syllabus": "普通高中历史课程标准（2017年版2022年修订）"
        }
    ]
    
    # 执行工作流测试
    final_context = None
    for test_input in test_inputs:
        print("\n" + "="*80)
        print(f"测试输入: {test_input['User_query']}")
        print(f"学科: {test_input['Subject']}")
        print(f"课程标准: {test_input['Syllabus']}")
        print("="*80)
        
        # 执行工作流
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 运行工作流
            final_context = workflow.run(test_input)
            
            # 计算运行时间
            execution_time = time.time() - start_time
            
            # 准备结果输出
            result_lines = []
            result_lines.append("-"*40)
            result_lines.append("工作流执行结果:")
            result_lines.append("-"*40)
            result_lines.append(f"问题: {final_context['User_query']}")
            
            # 如果是复杂问题，显示优化后的查询
            if 'Bettered_query' in final_context:
                result_lines.append(f"优化后的问题: {final_context['Bettered_query']}")
            
            result_lines.append(f"回答: {final_context['final_answer']}")
            
            # 显示分类结果
            if 'classification_result' in final_context:
                result_lines.append(f"问题类型: {final_context['classification_result']['class_name']}")
                result_lines.append(f"分类理由: {final_context['classification_result_reason']}")
            
            result_lines.append(f"执行时间: {execution_time:.2f}秒")
            
            # 输出到控制台
            for line in result_lines:
                if line.startswith("问题:"):
                    print(f"{Fore.GREEN}问题:{Style.RESET_ALL}{line[3:]}")
                elif line.startswith("优化后的问题:"):
                    print(f"{Fore.GREEN}优化后的问题:{Style.RESET_ALL}{line[7:]}")
                elif line.startswith("回答:"):
                    print(f"{Fore.GREEN}回答:{Style.RESET_ALL}{line[3:]}")
                elif line.startswith("问题类型:"):
                    print(f"{Fore.GREEN}问题类型:{Style.RESET_ALL}{line[5:]}")
                elif line.startswith("分类理由:"):
                    print(f"{Fore.GREEN}分类理由:{Style.RESET_ALL}{line[5:]}")
                elif line.startswith("执行时间:"):
                    print(f"{Fore.GREEN}执行时间:{Style.RESET_ALL}{line[5:]}")
                else:
                    print(line)
            
            # 保存结果到文件
            result_file = os.path.join(os.path.dirname(__file__), 'result.txt')
            with open(result_file, 'a', encoding='utf-8') as f:
                f.write("\n".join(result_lines))
                f.write("\n\n")
                
        except Exception as e:
            error_msg = f"\n工作流执行失败: {e}\n"
            print(f"{Fore.RED}{error_msg}{Style.RESET_ALL}")
            # 保存错误信息到文件
            result_file = os.path.join(os.path.dirname(__file__), 'result.txt')
            with open(result_file, 'a', encoding='utf-8') as f:
                f.write(error_msg)
                f.write("\n\n")
    
    completion_msg = "\n教育工作流演示执行完成！"
    print(f"{Fore.GREEN}{completion_msg}{Style.RESET_ALL}")
    # 保存完成信息到文件
    with open(result_file, 'a', encoding='utf-8') as f:
        f.write(completion_msg)
        f.write("\n" + "="*80 + "\n")
    
    return final_context  # 返回最后一次执行的上下文

if __name__ == "__main__":
    run_educational_workflow()
