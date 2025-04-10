"""
课堂测验代理 - 根据知识点生成问题，评估学生回答并提供学习建议。

工作流程:
1. 接收知识点输入
2. 生成相关的开放性测试问题
3. 显示问题给学生并收集回答
4. 对学生回答进行评分
5. 提供个性化学习建议和后续练习
"""
import sys
import os
import json
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
from src.workflow.nodes.json_extractor_node import JSONExtractorNode
from src.llm.deepseek_client import DeepSeekClient

# 初始化colorama
init(autoreset=True)

def create_classroom_quiz_workflow(llm_client):
    """创建课堂测验工作流"""
    
    # 开始节点
    start_node = StartNode(
        node_id="start",
        node_name="Start Node",
        output_variable_names=["keypoint"],
        next_node_id="quiz_generator"
    )
    
    # 生成测验节点
    quiz_generator = LLMNode(
        node_id="quiz_generator",
        node_name="Quiz Generator Node",
        system_prompt_template="""
        你是一名教育领域的专业出题老师，请根据以下知识点："{keypoint}"，出一道有深度的开放性问题。
        
        要求：
        1. 问题应该能测试学生对该知识点的理解深度
        2. 答案应包含清晰的得分点和评分标准
        
        请按照以下JSON格式输出，不要添加其他说明：
        ```
        {{
            "problem": "问题内容",
            "answer": {{
                "score_points": [
                    {{
                        "value": "Score value",
                        "rule": "Scoring rule"
                    }}
                ]
            }}
        }}  
        ```
        切记不要修改json的字段命名导致后续节点报错！
        """,
        output_variable_name="quiz_info",
        llm_client=llm_client,
        stream=True,                  # 启用流式传输
        stream_callback=stream_callback,  # 使用自定义回调
        next_node_id="json_extractor"
    )
    
    # JSON提取器节点
    json_extractor = JSONExtractorNode(
        node_id="json_extractor",
        node_name="JSON Extractor Node",
        input_variable_name="quiz_info",
        output_variable_name="quiz_info_extracted",
        schema={
            "type": "object",
            "properties": {
                "problem": {"type": "string"},
                "answer": {
                    "type": "object",
                    "properties": {
                        "score_points": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "value": {"type": "string"},
                                    "rule": {"type": "string"}
                                },
                                "required": ["value", "rule"]
                            }
                        }
                    },
                    "required": ["score_points"]
                }
            },
            "required": ["problem", "answer"]
        },
        default_value={"problem": "无法生成题目", "answer": {"score_points": []}},
        raise_on_error=False
    )
    
    # 用户输入节点
    user_input = InputNode(
        node_id="user_input",
        node_name="User Input Node",
        prompt_text="""
        请仔细阅读下面的题目，并提供您的答案：
        
        {quiz_info_extracted[problem]}
        """,
        output_variable_name="user_response",
        next_node_id="score_evaluation"
    )
    
    # 评分节点
    score_evaluation = LLMNode(
        node_id="score_evaluation",
        node_name="Score Evaluation Node",
        system_prompt_template="""
        你是一名公正严谨的教育评估专家。请对学生的答案进行评分。
        题目：{quiz_info_extracted[problem]}
        标准答案：{quiz_info_extracted[answer]}
        学生答案：{user_response}
        评分要求：
        1. 根据标准答案中的得分点进行客观评价
        2. 分数范围为0-100整数
        3. 详细说明得分理由和不足之处
        请使用以下JSON格式返回评分结果：
        {{
            "score_details": "详细的得分理由，包括优点和不足",
            "score": 分数值（0-100的整数）
        }}
        仅返回JSON格式结果，不要添加其他文字。
        """,
        output_variable_name="mark",
        llm_client=llm_client,
        stream=True,                  # 启用流式传输
        stream_callback=stream_callback,  # 使用自定义回调
        next_node_id="json_extractor_score"
    )
    
    # 评分JSON提取器节点
    json_extractor_score = JSONExtractorNode(
        node_id="json_extractor_score",
        node_name="Score JSON Extractor Node",
        input_variable_name="mark",
        output_variable_name="mark_extracted",
        schema={
            "type": "object",
            "properties": {
                "score_details": {"type": "string"},
                "score": {"type": "integer", "minimum": 0, "maximum": 100}
            },
            "required": ["score_details", "score"]
        },
        default_value={"score_details": "无法评分", "score": 0},
        raise_on_error=False
    )
    
    # 学习建议节点
    learning_suggestion = LLMNode(
        node_id="learning_suggestion",
        node_name="Learning Suggestion Node",
        system_prompt_template="""
        你是一个专业的教学助手，请根据学生的答题表现提供个性化学习建议。
        
        题目知识点：{keypoint}
        学生得分：{mark_extracted[score]}
        评分详情：{mark_extracted[score_details]}
        
        请提供以下内容：
        1. 对学生当前掌握情况的诊断
        2. 具体指出知识盲点或薄弱环节
        3. 提供针对性的学习建议和资源推荐
        4. 设计1-2个后续练习问题帮助巩固
        
        回复应当鼓励性、建设性，注重帮助学生取得进步。
        """,
        output_variable_name="suggestion",
        llm_client=llm_client,
        stream=True,                  # 启用流式传输
        stream_callback=stream_callback,  # 使用自定义回调
        next_node_id="end"
    )
    
    # 结束节点
    end_node = EndNode(
        node_id="end",
        node_name="End Node",
        input_variable_names=[
            "keypoint",
            "quiz_info_extracted",
            "user_response",
            "mark_extracted",
            "suggestion"
        ]
    )
    
    # 创建工作流
    workflow = Workflow([
        start_node,
        quiz_generator,
        json_extractor,
        user_input,
        score_evaluation,
        json_extractor_score,
        learning_suggestion,
        end_node
    ])
    
    return workflow

def stream_callback(text_chunk):
    """处理流式输出的文本片段"""
    print(text_chunk, end="", flush=True)

def run_classroom_quiz(keypoint=None):
    """运行课堂测验工作流"""
    
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
    llm_client = DeepSeekClient(api_key=api_key, model="deepseek-chat")

    print(f"{Fore.GREEN}已创建DeepSeek客户端，使用模型: {llm_client.model}{Style.RESET_ALL}")
    
    # 创建工作流
    workflow = create_classroom_quiz_workflow(llm_client)
    
    # 如果没有提供知识点，请求用户输入
    if not keypoint:
        keypoint = input(f"{Fore.CYAN}请输入要测试的知识点: {Style.RESET_ALL}")
    
    # 设置初始上下文
    context = {"keypoint": keypoint}
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 运行工作流
        final_context = workflow.run(context)
        
        # 计算运行时间
        execution_time = time.time() - start_time
        
        # 打印结果摘要
        print("\n" + "="*80)
        print(f"{Fore.GREEN}课堂测验执行完成{Style.RESET_ALL}")
        print(f"执行时间: {execution_time:.2f}秒")
        print("="*80 + "\n")
        
        # 显示知识点
        print(f"{Fore.CYAN}知识点:{Style.RESET_ALL} {final_context['keypoint']}")
        
        # 显示题目
        print(f"\n{Fore.CYAN}题目:{Style.RESET_ALL}")
        print(final_context['quiz_info_extracted']['problem'])
        
        # 显示学生回答
        print(f"\n{Fore.CYAN}学生回答:{Style.RESET_ALL}")
        print(final_context['user_response'])
        
        # 显示评分
        print(f"\n{Fore.CYAN}评分结果:{Style.RESET_ALL}")
        print(f"分数: {final_context['mark_extracted']['score']}")
        print(f"评分详情: {final_context['mark_extracted']['score_details']}")
        
        # 显示学习建议
        print(f"\n{Fore.CYAN}学习建议:{Style.RESET_ALL}")
        print(final_context['suggestion'])
        
        return final_context
        
    except Exception as e:
        print(f"\n{Fore.RED}工作流执行失败: {e}{Style.RESET_ALL}")
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    # 可以在这里提供默认的知识点，或者留空让用户输入
    sample_keypoint = ""  # 例如: "牛顿第二定律"
    run_classroom_quiz(sample_keypoint)
