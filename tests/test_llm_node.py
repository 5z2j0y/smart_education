import unittest
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow.nodes.llm_node import LLMNode
from src.llm.fake_client import FakeLLMClient

class TestLLMNode(unittest.TestCase):
    """测试LLMNode的功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建假LLM客户端
        self.fake_llm = FakeLLMClient()
        
        # 创建LLMNode实例
        self.llm_node = LLMNode(
            node_id="test_llm",
            node_name="Test LLM Node",
            system_prompt_template="Process this text: {input_text}",
            output_variable_name="processed_text",
            llm_client=self.fake_llm
        )
    
    def test_initialization(self):
        """测试LLMNode的初始化"""
        self.assertEqual(self.llm_node.node_id, "test_llm")
        self.assertEqual(self.llm_node.node_name, "Test LLM Node")
        self.assertEqual(self.llm_node.system_prompt_template, "Process this text: {input_text}")
        self.assertEqual(self.llm_node.output_variable_name, "processed_text")
        self.assertEqual(self.llm_node.input_variable_names, ["input_text"])
        self.assertEqual(str(self.llm_node), "LLMNode(id='test_llm', name='Test LLM Node')")
    
    def test_extract_variables_from_template(self):
        """测试从模板提取变量名"""
        # 单个变量
        template1 = "Hello {name}!"
        vars1 = self.llm_node._extract_variables_from_template(template1)
        self.assertEqual(vars1, ["name"])
        
        # 多个变量
        template2 = "Hello {name}, your age is {age} and your city is {city}."
        vars2 = self.llm_node._extract_variables_from_template(template2)
        self.assertCountEqual(vars2, ["name", "age", "city"])
        
        # 重复变量
        template3 = "Hello {name}! Nice to meet you, {name}."
        vars3 = self.llm_node._extract_variables_from_template(template3)
        self.assertEqual(vars3, ["name"])
        
        # 无变量
        template4 = "Hello world!"
        vars4 = self.llm_node._extract_variables_from_template(template4)
        self.assertEqual(vars4, [])
    
    def test_format_prompt(self):
        """测试格式化提示词模板"""
        # 创建具有单个变量的LLMNode
        node = LLMNode(
            node_id="format_test",
            node_name="Format Test",
            system_prompt_template="Process this: {input_text}",
            output_variable_name="result",
            llm_client=self.fake_llm
        )
        
        # 测试格式化
        context = {"input_text": "Hello world!"}
        formatted = node._format_prompt(context)
        self.assertEqual(formatted, "Process this: Hello world!")
        
        # 测试多个变量
        node2 = LLMNode(
            node_id="format_test2",
            node_name="Format Test 2",
            system_prompt_template="Hello {name}, you are {age} years old.",
            output_variable_name="result",
            llm_client=self.fake_llm
        )
        context2 = {"name": "John", "age": 30}
        formatted2 = node2._format_prompt(context2)
        self.assertEqual(formatted2, "Hello John, you are 30 years old.")
        
        # 测试缺失变量
        with self.assertRaises(ValueError) as context:
            node._format_prompt({})
        self.assertIn("Required variable 'input_text' not found", str(context.exception))
    
    def test_execute_with_valid_context(self):
        """测试使用有效上下文执行LLMNode"""
        # 创建上下文
        context = {"input_text": "Hello world!"}
        
        # 执行节点
        result = self.llm_node.execute(context)
        
        # 验证结果
        self.assertIn("input_text", result)
        self.assertIn("processed_text", result)
        self.assertEqual(result["input_text"], "Hello world!")
        self.assertTrue(result["processed_text"].startswith("LLM Simulation"))
    
    def test_execute_with_invalid_context(self):
        """测试使用缺少变量的上下文执行LLMNode"""
        # 创建空上下文
        empty_context = {}
        
        # 验证执行抛出异常
        with self.assertRaises(ValueError) as context:
            self.llm_node.execute(empty_context)
        
        # 验证异常消息
        self.assertIn("Required variable 'input_text' not found", str(context.exception))

if __name__ == "__main__":
    unittest.main()
