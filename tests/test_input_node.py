import unittest
from unittest.mock import patch
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow.nodes.input_node import InputNode

class TestInputNode(unittest.TestCase):
    """测试InputNode的功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建基本输入节点
        self.basic_node = InputNode(
            node_id="test_input",
            node_name="Test Input",
            prompt_text="输入测试:",
            output_variable_name="test_value"
        )
        
        # 创建带默认值的输入节点
        self.node_with_default = InputNode(
            node_id="default_input",
            node_name="Default Input",
            prompt_text="带默认值输入:",
            output_variable_name="default_value",
            default_value="默认文本"
        )
        
        # 创建带验证函数的输入节点
        self.node_with_validation = InputNode(
            node_id="validated_input",
            node_name="Validated Input",
            prompt_text="请输入数字:",
            output_variable_name="number_value",
            validation_func=lambda x: x.isdigit()
        )
        
        # 创建指定下一节点的输入节点
        self.node_with_next = InputNode(
            node_id="next_node_input",
            node_name="Input With Next",
            prompt_text="输入测试:",
            output_variable_name="test_value",
            next_node_id="next_test_node"
        )
    
    def test_initialization(self):
        """测试InputNode的初始化"""
        self.assertEqual(self.basic_node.node_id, "test_input")
        self.assertEqual(self.basic_node.node_name, "Test Input")
        self.assertEqual(self.basic_node.prompt_text, "输入测试:")
        self.assertEqual(self.basic_node.output_variable_name, "test_value")
        self.assertIsNone(self.basic_node.default_value)
        self.assertIsNone(self.basic_node.validation_func)
        self.assertIsNone(self.basic_node.next_node_id)
        self.assertEqual(str(self.basic_node), "InputNode(id='test_input', name='Test Input')")
    
    @patch('builtins.input', return_value="用户输入")
    def test_basic_input(self, mock_input):
        """测试基本输入功能"""
        context = {}
        result = self.basic_node.execute(context)
        
        # 验证结果
        self.assertEqual(result["test_value"], "用户输入")
        self.assertNotIn("next_node_id", result)
    
    @patch('builtins.input', return_value="")
    def test_default_value(self, mock_input):
        """测试默认值功能"""
        context = {}
        result = self.node_with_default.execute(context)
        
        # 验证结果 - 当用户输入为空时应使用默认值
        self.assertEqual(result["default_value"], "默认文本")
    
    @patch('builtins.input', side_effect=["abc", "123"])
    def test_validation(self, mock_input):
        """测试输入验证功能"""
        context = {}
        result = self.node_with_validation.execute(context)
        
        # 验证结果 - 应拒绝非数字输入并接受数字输入
        self.assertEqual(result["number_value"], "123")
        # 验证mock被调用两次（第一次输入无效，第二次有效）
        self.assertEqual(mock_input.call_count, 2)
    
    @patch('builtins.input', return_value="用户输入")
    def test_next_node_id(self, mock_input):
        """测试设置下一节点ID功能"""
        context = {}
        result = self.node_with_next.execute(context)
        
        # 验证结果 - 应包含正确的输入值和下一节点ID
        self.assertEqual(result["test_value"], "用户输入")
        self.assertEqual(result["next_node_id"], "next_test_node")
    
    @patch('builtins.input', return_value="新输入")
    def test_context_preservation(self, mock_input):
        """测试上下文保留功能"""
        # 创建包含已有变量的上下文
        context = {"existing_var": "现有值"}
        result = self.basic_node.execute(context)
        
        # 验证结果 - 应保留现有变量并添加新输入
        self.assertEqual(result["existing_var"], "现有值")
        self.assertEqual(result["test_value"], "新输入")

    @patch('builtins.input', side_effect=["", "有效输入"])
    def test_empty_input_no_default(self, mock_input):
        """测试无默认值时的空输入处理"""
        context = {}
        # 使用带验证函数的节点，但验证函数改为检查非空
        node = InputNode(
            node_id="empty_check",
            node_name="Empty Check",
            prompt_text="请输入非空内容:",
            output_variable_name="content",
            validation_func=lambda x: bool(x.strip())
        )
        result = node.execute(context)
        
        # 验证结果 - 应拒绝空输入并接受非空输入
        self.assertEqual(result["content"], "有效输入")
        self.assertEqual(mock_input.call_count, 2)

if __name__ == '__main__':
    unittest.main()
