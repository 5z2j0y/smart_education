"""
多步推理工作流示例。
演示如何使用框架构建一个多步推理工作流：
1. 分析问题
2. 生成解题步骤
3. 执行解题
4. 检查答案
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
from src.llm.deepseek_client import DeepSeekClient

def run_multi_step_reasoning():
    """运行多步推理工作流示例"""
    
    # 创建 DeepSeek LLM Client 实例
    # 请确保环境变量中设置了DEEPSEEK_API_KEY，或在此处直接提供
    api_key = os.environ.get("DEEPSEEK_API_KEY", "your_api_key_here")
    deepseek_llm = DeepSeekClient(api_key=api_key, model="deepseek-chat")

    # 定义节点
    # 开始节点 - 接收数学问题
    start_node = StartNode(
        node_id="start", 
        node_name="Start", 
        output_variable_names=["math_problem"]
    )
    
    # 问题分析节点
    analysis_node = LLMNode(
        node_id="analysis", 
        node_name="Problem Analyzer",
        system_prompt_template="分析以下数学问题的类型和难度: {math_problem}",
        output_variable_name="problem_analysis",
        llm_client=deepseek_llm
    )
    
    # 解题步骤生成节点
    planning_node = LLMNode(
        node_id="planning", 
        node_name="Solution Planner",
        system_prompt_template="根据分析，列出解决以下问题的步骤: {math_problem}\n分析: {problem_analysis}",
        output_variable_name="solution_steps",
        llm_client=deepseek_llm
    )
    
    # 执行解题节点
    solving_node = LLMNode(
        node_id="solving", 
        node_name="Problem Solver",
        system_prompt_template="按照以下步骤解决数学问题: {math_problem}\n步骤: {solution_steps}",
        output_variable_name="solution",
        llm_client=deepseek_llm
    )
    
    # 答案检查节点
    verification_node = LLMNode(
        node_id="verification", 
        node_name="Solution Verifier",
        system_prompt_template="检查以下解答是否正确: {solution}\n原问题: {math_problem}",
        output_variable_name="verification_result",
        llm_client=deepseek_llm
    )
    
    # 结束节点
    end_node = EndNode(
        node_id="end", 
        node_name="End", 
        input_variable_names=["solution", "verification_result"]
    )

    # 创建工作流
    workflow = Workflow(nodes=[
        start_node, 
        analysis_node, 
        planning_node, 
        solving_node, 
        verification_node, 
        end_node
    ])

    # 定义初始输入
    initial_input = {"math_problem": "一个水箱，上底面积是3平方米，下底面积是5平方米，高是2米，里面的水深是1.5米，求水的体积是多少?"}

    # 运行工作流
    print("\n开始执行多步推理工作流...")
    final_context = workflow.run(initial_input)

    # 输出结果
    print("\n=== 多步推理工作流结果 ===")
    print(f"问题: {final_context['math_problem']}")
    print(f"分析: {final_context['problem_analysis']}")
    print(f"解题步骤: {final_context['solution_steps']}")
    print(f"解答: {final_context['solution']}")
    print(f"验证结果: {final_context['verification_result']}")
    
    print("\n多步推理工作流执行完成！")
    return final_context

if __name__ == "__main__":
    run_multi_step_reasoning()
