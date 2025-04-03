import unittest
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow.engine import Workflow
from src.workflow.nodes.start_node import StartNode
from src.workflow.nodes.end_node import EndNode

class TestWorkflow(unittest.TestCase):
    """测试Workflow执行器的功能"""
    
    def test_initialization_empty(self):
        """测试创建空节点列表的工作流，应该抛出异常"""
        with self.assertRaises(ValueError) as context:
            Workflow([])
        self.assertIn("must contain at least one node", str(context.exception))
    
    def test_initialization_valid(self):
        """测试创建有效的工作流"""
        # 创建开始和结束节点
        start_node = StartNode("start", "Start Node", ["input_data"])
        end_node = EndNode("end", "End Node", ["input_data"])
        
        # 创建工作流
        workflow = Workflow([start_node, end_node])
        
        # 验证节点列表
        self.assertEqual(len(workflow.nodes), 2)
        self.assertEqual(workflow.nodes[0], start_node)
        self.assertEqual(workflow.nodes[1], end_node)
    
    def test_warning_no_start_node(self):
        """测试创建不以StartNode开始的工作流，应该显示警告"""
        # 由于警告是打印到标准输出的，我们不能直接断言
        # 这里只是确保代码不会抛出异常
        end_node1 = EndNode("end1", "End Node 1", ["input_data"])
        end_node2 = EndNode("end2", "End Node 2", ["input_data"])
        
        # 创建工作流，应打印警告信息但不抛出异常
        workflow = Workflow([end_node1, end_node2])
        self.assertEqual(len(workflow.nodes), 2)
    
    def test_run_successful(self):
        """测试成功执行工作流"""
        # 创建开始和结束节点
        start_node = StartNode("start", "Start Node", ["input_data"])
        end_node = EndNode("end", "End Node", ["input_data"])
        
        # 创建工作流
        workflow = Workflow([start_node, end_node])
        
        # 运行工作流
        initial_context = {"input_data": "Hello, Workflow!"}
        result = workflow.run(initial_context)
        
        # 验证结果
        self.assertEqual(result, {"input_data": "Hello, Workflow!"})
    
    def test_run_failure(self):
        """测试执行失败的工作流"""
        # 创建开始和结束节点
        start_node = StartNode("start", "Start Node", ["input_data"])
        end_node = EndNode("end", "End Node", ["input_data"])
        
        # 创建工作流
        workflow = Workflow([start_node, end_node])
        
        # 运行工作流，使用空上下文应该导致StartNode失败
        with self.assertRaises(ValueError) as context:
            workflow.run({})
        
        # 验证异常消息
        self.assertIn("Expected initial variable 'input_data' not found", str(context.exception))

if __name__ == "__main__":
    unittest.main()
