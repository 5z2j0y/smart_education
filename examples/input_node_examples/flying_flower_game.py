"""
成语接龙游戏示例。
演示如何使用InputNode和IterativeWorkflowNode创建互动游戏工作流。

在这个成语接龙游戏中，用户和AI轮流接龙成语，要求每个成语首字与上一个成语末字相同，共进行5轮。
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
from src.workflow.nodes.llm_node import LLMNode
from src.workflow.nodes.end_node import EndNode
from src.workflow.nodes.input_node import InputNode
from src.workflow.nodes.iterative_workflow_node import IterativeWorkflowNode
from src.llm.deepseek_client import DeepSeekClient

# 初始化colorama
init(autoreset=True)

def run_flying_flower_game():
    """运行成语接龙游戏工作流示例"""
    
    print(f"{Fore.CYAN}=== 成语接龙游戏 ==={Style.RESET_ALL}")
    print("规则：用户和AI轮流接龙成语，要求每个成语首字与上一个成语末字相同，共进行3轮")
    
    # 从环境变量中获取API密钥
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误: 请设置DEEPSEEK_API_KEY环境变量")
        exit(1)
    
    # 创建DeepSeekClient实例
    deepseek_llm = DeepSeekClient(api_key=api_key, model="deepseek-chat")
    
    # ====== 创建成语接龙游戏的节点 ======
    
    # 子工作流的开始节点（每轮迭代起点）
    round_start = StartNode(
        node_id="round_start",
        node_name="Round Start",
        output_variable_names=["round_number", "previous_idiom"]  # 修改输出变量
    )
    
    # 用户输入成语节点
    user_input = InputNode(
        node_id="user_input",
        node_name="User Idiom Input",
        prompt_text="请输入一个成语（第一轮可任意输入；后续成语首字需与上个成语末字相同）：",
        output_variable_name="user_idiom",
        validation_func=lambda x: True  # 仅作简单验证，可按需扩展
    )
    
    # AI回应成语节点
    ai_response = LLMNode(
        node_id="ai_response",
        node_name="AI Idiom Response",
        system_prompt_template="""
        这是一个成语接龙游戏，请根据以下信息生成回应:
        
        当前轮数: {round_number}
        上一个成语: {previous_idiom}
        用户成语: {user_idiom}
        
        请回复一个成语，其首字必须与上一个成语的最后一个字相同。如果是第一轮，请随意生成一个成语。
        """,
        output_variable_name="ai_idiom",
        llm_client=deepseek_llm
    )
    
    # 回合总结节点
    round_summary = LLMNode(
        node_id="round_summary",
        node_name="Round Summary",
        system_prompt_template="""
        总结这一轮成语接龙：
        
        轮数: {round_number}
        上一成语: {previous_idiom}
        用户成语: {user_idiom}
        AI成语: {ai_idiom}
        
        请用一句话评价这一轮的对接。
        """,
        output_variable_name="round_summary",
        llm_client=deepseek_llm
    )
    
    # 创建迭代工作流节点（控制5轮成语接龙）
    chengyu_game = IterativeWorkflowNode(
        node_id="chengyu_game",
        node_name="Chengyu Game",
        nodes=[round_start, user_input, ai_response, round_summary],
        condition_function=lambda context: context.get("_iteration_count", 0) < 3,
        max_iterations=3,
        # 主工作流到子工作流的变量映射
        input_mapping={
            "previous_idiom": "previous_idiom",
            "current_round": "round_number"
        },
        # 迭代间变量传递，将AI的成语作为下一轮的“previous_idiom”
        iteration_mapping={
            "round_number": "round_number",
            "previous_idiom": "previous_idiom",
            "ai_idiom": "previous_idiom",
            "_iteration_count": "_iteration_count"
        },
        # 子工作流到主工作流的变量映射
        output_mapping={
            "user_idiom": "final_user_idiom",
            "ai_idiom": "final_ai_idiom",
            "round_summary": "final_summary"
        },
        result_collection_mode="append",
        result_variable="game_history",
        next_node_id="game_conclusion"
    )
    
    # 主工作流的开始节点
    start_node = StartNode(
        node_id="start",
        node_name="Game Start",
        output_variable_names=["previous_idiom"]  # 修改输出变量
    )
    
    # 游戏总结节点
    game_conclusion = LLMNode(
        node_id="game_conclusion",
        node_name="Game Conclusion",
        system_prompt_template="""
        请总结这场成语接龙游戏，并评价双方表现。
        
        总轮数: {_iterations_completed}
        
        用户最后的成语: {final_user_idiom}
        AI最后的成语: {final_ai_idiom}
        最后一轮评价: {final_summary}
        
        请给出游戏总结和鼓励性的评价。
        """,
        output_variable_name="game_conclusion",
        llm_client=deepseek_llm
    )
    
    # 结束节点
    end_node = EndNode(
        node_id="end",
        node_name="Game End",
        input_variable_names=[
            "previous_idiom",
            "final_user_idiom", 
            "final_ai_idiom",
            "final_summary",
            "game_conclusion",
            "game_history",
            "_iterations_completed"
        ]
    )
    
    # 创建主工作流
    workflow = Workflow([
        start_node,
        chengyu_game,
        game_conclusion,
        end_node
    ])
    
    # 设置初始上下文 - 初始 previous_idiom 为空，用户可任意输入第一个成语
    context = {
        "previous_idiom": "",
        "current_round": 1
    }
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 运行工作流
        final_context = workflow.run(context)
        
        # 计算运行时间
        execution_time = time.time() - start_time
        
        # 打印游戏结果
        print("\n" + "="*50)
        print(f"{Fore.GREEN}成语接龙游戏结束!{Style.RESET_ALL}")
        print(f"完成轮数: {final_context['_iterations_completed']}")
        print(f"用时: {execution_time:.2f}秒")
        
        # 打印游戏历史
        print("\n" + "="*50)
        print(f"{Fore.CYAN}游戏回顾:{Style.RESET_ALL}")
        for i, round_data in enumerate(final_context["game_history"]):
            print(f"\n{Fore.YELLOW}第 {i+1} 轮:{Style.RESET_ALL}")
            print(f"用户: {final_context['game_history'][i]['user_idiom']}")
            print(f"AI: {final_context['game_history'][i]['ai_idiom']}")
            
        # 打印游戏总结
        print("\n" + "="*50)
        print(f"{Fore.GREEN}游戏总结:{Style.RESET_ALL}")
        print(final_context["game_conclusion"])
        
    except Exception as e:
        print(f"\n{Fore.RED}工作流执行出错: {e}{Style.RESET_ALL}")
        import traceback
        print(traceback.format_exc())
    
    print(f"\n{Fore.CYAN}成语接龙游戏示例执行完毕!{Style.RESET_ALL}")

if __name__ == "__main__":
    run_flying_flower_game()
