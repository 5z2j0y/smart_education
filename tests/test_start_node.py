import unittest
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow.nodes.start_node import StartNode

class TestStartNode(unittest.TestCase):
    """测试StartNode的功能"""
    
    def test_initialization(self):
        """测试StartNode的初始化"""
        # 创建StartNode实例
        start_node = StartNode("start", "Start Node", ["user_query"])
        
        # 验证属性
        self.assertEqual(start_node.node_id, "start")
        self.assertEqual(start_node.node_name, "Start Node")
        self.assertEqual(start_node.output_variable_names, ["user_query"])
        
        # 验证字符串表示
        self.assertEqual(str(start_node), "StartNode(id='start', name='Start Node')")
    
    def test_execute_with_valid_context(self):
        """测试使用有效上下文执行StartNode"""
        # 创建StartNode实例
        start_node = StartNode("start", "Start Node", ["user_query"])
        
        # 提供包含所需变量的上下文
        context = {"user_query": "什么是人工智能？"}
        result = start_node.execute(context)
        
        # 验证上下文未被修改
        self.assertEqual(result, context)
    
    def test_execute_with_invalid_context(self):
        """测试使用缺少变量的上下文执行StartNode，应该抛出异常"""
        # 创建StartNode实例
        start_node = StartNode("start", "Start Node", ["user_query"])
        
        # 提供一个空上下文
        empty_context = {}
        
        # 验证执行抛出异常
        with self.assertRaises(ValueError) as context:
            start_node.execute(empty_context)
        
        # 验证异常消息
        self.assertIn("Expected initial variable 'user_query' not found", str(context.exception))

if __name__ == "__main__":
    unittest.main()
