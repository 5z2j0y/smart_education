import unittest
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow.nodes.conditional_branch_node import ConditionalBranchNode, ClassDefinition
from src.llm.fake_client import FakeLLMClient

class TestConditionalBranchNode(unittest.TestCase):
    """测试ConditionalBranchNode的功能"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建假LLM客户端
        self.fake_llm = FakeLLMClient()
        
        # 自定义响应
        original_invoke = self.fake_llm.invoke
        def custom_invoke(prompt):
            if "专业的问题分类器" in prompt:
                input_text = prompt.split("输入问题:")[-1].strip()
                if input_text == "...":  # 明确处理模糊输入
                    return """{"class_name": "General", "confidence": 0.70, "reason": "无法明确分类的一般性问题"}"""
                elif "数学" in input_text or "学习" in input_text:
                    return """{"class_name": "Educational", "confidence": 0.95, "reason": "这是一个关于教育和学习的问题"}"""
                elif "天气" in input_text or "饭" in input_text:
                    return """{"class_name": "Daily", "confidence": 0.90, "reason": "这是一个日常生活相关的问题"}"""
                else:
                    return """{"class_name": "General", "confidence": 0.70, "reason": "无法明确分类的一般性问题"}"""
            return original_invoke(prompt)
        
        self.fake_llm.invoke = custom_invoke
        
        # 定义分类
        self.classes = [
            ClassDefinition(
                name="Educational",
                description="教育相关的提问或陈述",
                next_node_id="educational_handler",
                examples=["什么是微积分?", "如何学好英语?"]
            ),
            ClassDefinition(
                name="Daily",
                description="日常生活对话",
                next_node_id="daily_handler",
                examples=["今天天气真好", "晚饭吃什么?"]
            )
        ]
        
        # 定义默认分类
        self.default_class = ClassDefinition(
            name="General",
            description="无法明确分类的一般对话",
            next_node_id="general_handler"
        )
        
        # 创建条件分支节点
        self.branch_node = ConditionalBranchNode(
            node_id="test_branch",
            node_name="Test Branch Node",
            classes=self.classes,
            input_variable_name="user_query",
            llm_client=self.fake_llm,
            default_class=self.default_class,
            output_reason=True
        )
    
    def test_initialization(self):
        """测试节点初始化"""
        self.assertEqual(self.branch_node.node_id, "test_branch")
        self.assertEqual(self.branch_node.node_name, "Test Branch Node")
        self.assertEqual(len(self.branch_node.classes), 2)
        self.assertEqual(self.branch_node.input_variable_name, "user_query")
        self.assertEqual(self.branch_node.output_variable_name, "classification_result")
        self.assertEqual(self.branch_node.default_class, self.default_class)
        self.assertTrue(self.branch_node.output_reason)
    
    def test_empty_classes_error(self):
        """测试空分类列表应该抛出错误"""
        with self.assertRaises(ValueError):
            ConditionalBranchNode(
                node_id="error_node",
                node_name="Error Node",
                classes=[],  # 空列表
                input_variable_name="query",
                llm_client=self.fake_llm
            )
    
    def test_duplicate_class_names_error(self):
        """测试重复的分类名称应该抛出错误"""
        with self.assertRaises(ValueError):
            ConditionalBranchNode(
                node_id="error_node",
                node_name="Error Node",
                classes=[
                    ClassDefinition("test", "Test 1", "node1"),
                    ClassDefinition("test", "Test 2", "node2")  # 重复名称
                ],
                input_variable_name="query",
                llm_client=self.fake_llm
            )
    
    def test_educational_classification(self):
        """测试教育类问题的分类"""
        context = {"user_query": "如何学好数学?"}
        result = self.branch_node.execute(context)
        
        self.assertIn("classification_result", result)
        self.assertIn("next_node_id", result)
        self.assertEqual(result["classification_result"]["class_name"], "Educational")
        self.assertEqual(result["next_node_id"], "educational_handler")
        self.assertIn("classification_result_reason", result)  # 因为output_reason=True
    
    def test_daily_classification(self):
        """测试日常类问题的分类"""
        context = {"user_query": "今天天气怎么样?"}
        result = self.branch_node.execute(context)
        
        self.assertEqual(result["classification_result"]["class_name"], "Daily")
        self.assertEqual(result["next_node_id"], "daily_handler")
    
    def test_default_classification(self):
        """测试默认分类"""
        context = {"user_query": "..."}
        result = self.branch_node.execute(context)
        
        self.assertEqual(result["classification_result"]["class_name"], "General")
        self.assertEqual(result["next_node_id"], "general_handler")
    
    def test_missing_input_variable(self):
        """测试缺少输入变量"""
        empty_context = {}
        with self.assertRaises(ValueError):
            self.branch_node.execute(empty_context)
    
    def test_no_default_class_error(self):
        """测试无默认分类时处理未知分类的错误"""
        # 创建一个没有默认分类的节点
        no_default_node = ConditionalBranchNode(
            node_id="no_default",
            node_name="No Default Node",
            classes=self.classes,
            input_variable_name="user_query",
            llm_client=self.fake_llm
        )
        
        # 模拟LLM返回未知分类
        def bad_invoke(prompt):
            return """{"class_name": "Unknown", "confidence": 0.5}"""
        
        no_default_node.llm_client.invoke = bad_invoke
        
        with self.assertRaises(ValueError):
            no_default_node.execute({"user_query": "test"})

if __name__ == "__main__":
    unittest.main()
