"""
子工作流节点的单元测试。
"""
import unittest
import sys
import os
import json

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow.nodes.start_node import StartNode
from src.workflow.nodes.llm_node import LLMNode
from src.workflow.nodes.end_node import EndNode
from src.workflow.nodes.conditional_branch_node import ConditionalBranchNode, ClassDefinition
from src.workflow.nodes.subworkflow_node import SubWorkflowNode
from src.workflow.engine import Workflow

# 创建一个模拟LLM客户端用于测试
class MockLLMClient:
    """模拟LLM客户端，用于测试"""
    
    def __init__(self):
        self.classification_response = None
    
    def get_response(self, prompt):
        """返回一个简单的响应"""
        return f"Mock response for: {prompt}"
    
    def invoke(self, prompt):
        """模拟LLM调用"""
        if self.classification_response:
            # 返回字符串形式的JSON，而不是Python对象
            return self.classification_response
        return self.get_response(prompt)
    
    def set_classification_response(self, class_name):
        """设置分类响应"""
        # 创建完整的JSON字符串响应
        self.classification_response = json.dumps({
            "class_name": class_name, 
            "confidence": 0.9, 
            "reason": "Test reason"
        })


class TestSubWorkflowNode(unittest.TestCase):
    """测试SubWorkflowNode的功能"""

    def test_basic_subworkflow(self):
        """测试基本子工作流功能"""
        # 创建模拟LLM客户端
        mock_llm = MockLLMClient()
        
        # 创建子工作流节点
        start_node = StartNode("sub_start", "Sub Start", ["input_value"])
        process_node = LLMNode("sub_process", "Sub Process", 
                             system_prompt_template="Process: {input_value}",
                             output_variable_name="processed_value",
                             llm_client=mock_llm)
        end_node = EndNode("sub_end", "Sub End", ["processed_value"])
        
        # 创建子工作流节点
        sub_workflow = SubWorkflowNode(
            node_id="test_sub",
            node_name="Test SubWorkflow",
            nodes=[start_node, process_node, end_node],
            input_mapping={"main_input": "input_value"},
            output_mapping={"processed_value": "main_output"},
            next_node_id="next_main_node"
        )
        
        # 执行子工作流节点
        result = sub_workflow.execute({"main_input": "test data"})
        
        # 验证结果
        self.assertIn("main_output", result)
        self.assertEqual(result["main_output"], mock_llm.get_response("Process: test data"))
        self.assertEqual(result["next_node_id"], "next_main_node")

    def test_auto_exit_detection(self):
        """测试自动出口节点检测功能"""
        # 创建模拟LLM客户端
        mock_llm = MockLLMClient()
        
        # 创建子工作流节点，不指定exit_node_id
        node1 = StartNode("node1", "Node 1", ["input"])
        node2 = LLMNode("node2", "Node 2", 
                       system_prompt_template="Process: {input}",
                       output_variable_name="output",
                       llm_client=mock_llm)
        # 不指定next_node_id，应该自动被识别为出口节点
        
        # 创建子工作流节点
        auto_exit_workflow = SubWorkflowNode(
            node_id="auto_exit",
            node_name="Auto Exit Workflow",
            nodes=[node1, node2],
            input_mapping={"main_input": "input"},
            output_mapping={"output": "main_output"},
            next_node_id="main_next"
        )
        
        # 执行子工作流节点
        result = auto_exit_workflow.execute({"main_input": "test data"})
        
        # 验证结果
        self.assertIn("main_output", result)
        self.assertEqual(result["next_node_id"], "main_next")

    def test_entry_node_specification(self):
        """测试指定入口节点功能"""
        # 创建模拟LLM客户端
        mock_llm = MockLLMClient()
        
        # 创建多个节点
        start_node = StartNode("start", "Start", ["input"])
        process1 = LLMNode("process1", "Process 1", 
                          system_prompt_template="Process1: {input}",
                          output_variable_name="output1",
                          llm_client=mock_llm)
        process2 = LLMNode("process2", "Process 2", 
                          system_prompt_template="Process2: {input}",
                          output_variable_name="output2",
                          llm_client=mock_llm)
        
        # 创建子工作流节点，指定process2为入口节点
        entry_workflow = SubWorkflowNode(
            node_id="entry_test",
            node_name="Entry Test Workflow",
            nodes=[start_node, process1, process2],
            input_mapping={"main_input": "input"},
            output_mapping={"output2": "main_output"},
            entry_node_id="process2",  # 跳过process1，直接从process2开始
            next_node_id="main_next"
        )
        
        # 执行子工作流节点
        result = entry_workflow.execute({"main_input": "test data"})
        
        # 验证结果 - 应该只执行process2
        self.assertIn("main_output", result)
        self.assertEqual(result["main_output"], mock_llm.get_response("Process2: test data"))
        # 输出应该不包含output1，因为process1没有执行
        self.assertNotIn("output1", result)
    
    def test_validation_errors(self):
        """测试节点验证功能"""
        # 测试空节点列表
        with self.assertRaises(ValueError):
            SubWorkflowNode("empty", "Empty Workflow", [])
        
        # 测试重复节点ID
        node1 = StartNode("same_id", "Node 1", ["input"])
        node2 = LLMNode("same_id", "Node 2", 
                       system_prompt_template="Process: {input}",
                       output_variable_name="output",
                       llm_client=MockLLMClient())
        
        with self.assertRaises(ValueError):
            SubWorkflowNode("duplicate", "Duplicate IDs", [node1, node2])
        
        # 测试不存在的入口节点
        node3 = StartNode("node3", "Node 3", ["input"])
        with self.assertRaises(ValueError):
            SubWorkflowNode("bad_entry", "Bad Entry", [node3], 
                          entry_node_id="non_existent")
        
        # 测试不存在的出口节点
        with self.assertRaises(ValueError):
            SubWorkflowNode("bad_exit", "Bad Exit", [node3], 
                          exit_node_id="non_existent")


if __name__ == "__main__":
    unittest.main()
