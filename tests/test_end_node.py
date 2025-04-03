import unittest
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow.nodes.end_node import EndNode

class TestEndNode(unittest.TestCase):
    
    def test_initialization(self):
        """测试EndNode初始化"""
        # 创建EndNode实例，期望从上下文中提取"result"变量
        end_node = EndNode("end", "End Node", ["result"])
        self.assertEqual(end_node.node_id, "end")
        self.assertEqual(end_node.node_name, "End Node")
        self.assertEqual(end_node.input_variable_names, ["result"])
        self.assertEqual(str(end_node), "EndNode(id='end', name='End Node')")
    
    def test_execute_with_valid_context(self):
        """测试使用有效上下文执行EndNode"""
        # 创建EndNode实例
        end_node = EndNode("end", "End Node", ["result"])
        
        # 提供包含所需变量的上下文
        context = {"result": "这是最终结果", "other_data": "其他数据"}
        result = end_node.execute(context)
        
        # 验证上下文正确传递
        self.assertEqual(result, context)
        
    def test_execute_with_missing_variables(self):
        """测试使用缺少必要变量的上下文执行EndNode"""
        # 创建EndNode实例
        end_node = EndNode("end", "End Node", ["result", "summary"])
        
        # 提供缺少部分所需变量的上下文
        incomplete_context = {"result": "这是最终结果", "other_data": "其他数据"}
        
        # 应该抛出ValueError异常
        with self.assertRaises(ValueError) as context:
            end_node.execute(incomplete_context)
        
        # 验证异常消息
        self.assertIn("Expected final variable 'summary' not found", str(context.exception))

if __name__ == "__main__":
    unittest.main()
