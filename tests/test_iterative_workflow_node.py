"""测试迭代工作流节点功能"""
import sys
import os
import json
import unittest
from unittest.mock import MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow.base import WorkflowContext
from src.workflow.nodes.start_node import StartNode
from src.workflow.nodes.llm_node import LLMNode
from src.workflow.nodes.end_node import EndNode
from src.workflow.nodes.iterative_workflow_node import IterativeWorkflowNode
from src.workflow.engine import Workflow


class MockLLMClient:
    """模拟LLM客户端，用于测试"""
    
    def __init__(self):
        self.responses = []
        self.current_index = 0
    
    def set_response_sequence(self, responses):
        """设置预定义的响应序列"""
        self.responses = responses
        self.current_index = 0
    
    def invoke(self, prompt):
        """返回预设响应序列中的下一个响应"""
        if not self.responses:
            return "Mock response"
        
        response = self.responses[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.responses)
        return response
    
    def get_response(self, prompt):
        """返回对特定提示的响应"""
        return f"Response to: {prompt}"


class TestIterativeWorkflowNode(unittest.TestCase):
    """迭代工作流节点测试类"""
    
    def test_basic_iteration(self):
        """测试基本迭代功能"""
        # 创建模拟LLM客户端
        mock_llm = MockLLMClient()
        
        # 设置模拟响应
        mock_llm.set_response_sequence([
            "Improved text 1",  # 第一次迭代的改进文本
            '{"quality_score": 0.5, "feedback": "Still needs work"}',  # 第一次评估
            "Improved text 2",  # 第二次迭代
            '{"quality_score": 0.9, "feedback": "Much better"}',  # 第二次评估达到阈值
        ])
        
        # 定义迭代条件
        def iteration_condition(context):
            # 从评估结果中提取质量分数
            if "evaluation" in context:
                try:
                    eval_data = json.loads(context["evaluation"])
                    return eval_data.get("quality_score", 0) < 0.8
                except:
                    return False
            return True  # 首次迭代时没有评估结果，默认继续
        
        # 创建节点
        start_node = StartNode("iter_start", "Iteration Start", ["content"])
        improve_node = LLMNode("improve", "Improve Content", 
                              system_prompt_template="Improve: {content}",
                              output_variable_name="improved_content",
                              llm_client=mock_llm)
        evaluate_node = LLMNode("evaluate", "Evaluate Content", 
                               system_prompt_template="Evaluate: {improved_content}",
                               output_variable_name="evaluation",
                               llm_client=mock_llm)
        
        # 创建迭代工作流节点
        iterative_node = IterativeWorkflowNode(
            node_id="iterative_test",
            node_name="Test Iteration",
            nodes=[start_node, improve_node, evaluate_node],
            condition_function=iteration_condition,
            max_iterations=5,
            input_mapping={"input_text": "content"},
            iteration_mapping={"improved_content": "content"},
            output_mapping={"improved_content": "final_content", "evaluation": "final_evaluation"},
            result_collection_mode="append",
            result_variable="iteration_history",
            next_node_id="next_main_node"
        )
        
        # 执行节点
        result = iterative_node.execute({"input_text": "Initial text"})
        
        # 验证结果
        self.assertEqual(result["final_content"], "Improved text 2")
        self.assertIn("_iterations_completed", result)
        self.assertEqual(result["_iterations_completed"], 2)
        self.assertIn("iteration_history", result)
        self.assertGreaterEqual(len(result["iteration_history"]), 1)
        self.assertEqual(result["next_node_id"], "next_main_node")
    
    def test_max_iterations_limit(self):
        """测试最大迭代次数限制"""
        # 创建模拟LLM客户端
        mock_llm = MockLLMClient()
        
        # 设置模拟响应 - 每次都返回相同的低质量结果
        mock_llm.set_response_sequence([
            "Attempt 1", '{"quality_score": 0.3}',
            "Attempt 2", '{"quality_score": 0.4}',
            "Attempt 3", '{"quality_score": 0.5}',
            "Attempt 4", '{"quality_score": 0.6}',  # 不应到达此处
        ])
        
        # 定义总是返回True的条件（迭代永不停止，应受最大次数限制）
        def always_continue(context):
            return True
        
        # 创建节点
        start_node = StartNode("iter_start", "Iteration Start", ["content"])
        process_node = LLMNode("process", "Process Content", 
                              system_prompt_template="Process: {content}",
                              output_variable_name="processed_content",
                              llm_client=mock_llm)
        evaluate_node = LLMNode("evaluate", "Evaluate Content", 
                               system_prompt_template="Evaluate: {processed_content}",
                               output_variable_name="evaluation",
                               llm_client=mock_llm)
        
        # 创建迭代工作流节点
        iterative_node = IterativeWorkflowNode(
            node_id="max_iter_test",
            node_name="Max Iterations Test",
            nodes=[start_node, process_node, evaluate_node],
            condition_function=always_continue,
            max_iterations=3,  # 最多执行3次迭代
            input_mapping={"input_text": "content"},
            iteration_mapping={"processed_content": "content"},
            output_mapping={"processed_content": "final_content"},
            result_collection_mode="replace",
            next_node_id="next_node"
        )
        
        # 执行节点
        result = iterative_node.execute({"input_text": "Initial text"})
        
        # 验证结果 - 应该在达到最大迭代次数后停止
        self.assertEqual(result["_iterations_completed"], 3)
        self.assertEqual(result["final_content"], "Attempt 3")
    
    def test_result_collection_modes(self):
        """测试不同的结果收集模式"""
        # 创建模拟LLM客户端
        mock_llm = MockLLMClient()
        
        # 定义只执行一次的条件函数，用于简化测试
        def run_once(context):
            return context.get("_iteration_count", 0) < 1
        
        # 创建基本节点
        start_node = StartNode("start", "Start", ["input"])
        process_node = LLMNode("process", "Process", 
                             system_prompt_template="Process: {input}",
                             output_variable_name="output",
                             llm_client=mock_llm)
        
        # 测试替换模式
        mock_llm.invoke = MagicMock(return_value='{"key": "value"}')
        replace_node = IterativeWorkflowNode(
            node_id="replace_test",
            node_name="Replace Mode Test",
            nodes=[start_node, process_node],
            condition_function=run_once,
            result_collection_mode="replace",
            result_variable="result",
            input_mapping={"text": "input"},
            output_mapping={"output": "processed_output"}
        )
        # 执行节点
        replace_result = replace_node.execute({"text": "test"})
        # 验证结果
        self.assertIn("processed_output", replace_result)
        
        # 测试追加模式
        append_node = IterativeWorkflowNode(
            node_id="append_test",
            node_name="Append Mode Test",
            nodes=[start_node, process_node],
            condition_function=run_once,
            result_collection_mode="append",
            result_variable="results",
            input_mapping={"text": "input"},
            output_mapping={"output": "processed_output"}
        )
        # 执行节点
        append_result = append_node.execute({"text": "test"})
        # 验证结果
        self.assertIn("processed_output", append_result)
        
        # 测试合并模式
        mock_llm.invoke = MagicMock(return_value='{"key1": "value1", "key2": "value2"}')
        merge_node = IterativeWorkflowNode(
            node_id="merge_test",
            node_name="Merge Mode Test",
            nodes=[start_node, process_node],
            condition_function=run_once,
            result_collection_mode="merge",
            result_variable="merged_result",
            input_mapping={"text": "input"},
            output_mapping={"output": "processed_output"}
        )
        # 执行节点
        merge_result = merge_node.execute({"text": "test"})
        # 验证结果
        self.assertIn("processed_output", merge_result)


if __name__ == "__main__":
    unittest.main()
