import unittest
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.workflow.nodes.json_extractor_node import JSONExtractorNode

class TestJSONExtractorNode(unittest.TestCase):
    """测试JSONExtractorNode的功能"""
    
    def test_basic_extraction(self):
        """测试基本JSON提取功能"""
        # 创建JSONExtractorNode实例
        extractor = JSONExtractorNode(
            node_id="json_test",
            node_name="JSON Extractor",
            input_variable_name="llm_output",
            output_variable_name="parsed_json"
        )
        
        # 测试有效的JSON提取
        context = {
            "llm_output": "Here's your data: { \"name\": \"Alice\", \"age\": 30 } Thank you!"
        }
        result = extractor.execute(context)
        self.assertIn("parsed_json", result)
        self.assertEqual(result["parsed_json"]["name"], "Alice")
        self.assertEqual(result["parsed_json"]["age"], 30)
    
    def test_schema_validation(self):
        """测试模式验证功能"""
        try:
            from jsonschema import validate
            has_jsonschema = True
        except ImportError:
            has_jsonschema = False
            self.skipTest("jsonschema package not installed")
        
        if has_jsonschema:
            # 创建带有schema的提取器
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "number"}
                },
                "required": ["name", "age"]
            }
            
            schema_extractor = JSONExtractorNode(
                node_id="schema_test",
                node_name="Schema JSON Extractor",
                input_variable_name="llm_output",
                output_variable_name="validated_json",
                schema=schema
            )
            
            # 测试有效数据
            valid_context = {
                "llm_output": "{ \"name\": \"Bob\", \"age\": 25 }"
            }
            result = schema_extractor.execute(valid_context)
            self.assertEqual(result["validated_json"]["name"], "Bob")
            
            # 测试无效数据（应该失败）
            invalid_context = {
                "llm_output": "{ \"name\": \"Bob\" }"  # 缺少必需的age字段
            }
            with self.assertRaises(ValueError):
                schema_extractor.execute(invalid_context)
    
    def test_error_handling(self):
        """测试错误处理策略"""
        # 创建带有默认值的提取器
        default_extractor = JSONExtractorNode(
            node_id="default_test",
            node_name="Default JSON Extractor",
            input_variable_name="llm_output",
            output_variable_name="json_data",
            default_value={"status": "error"},
            raise_on_error=False
        )
        
        # 测试无效输入
        invalid_context = {
            "llm_output": "This is not JSON"
        }
        result = default_extractor.execute(invalid_context)
        self.assertEqual(result["json_data"]["status"], "error")
        
        # 测试无输入变量
        missing_var_context = {}
        with self.assertRaises(ValueError):
            default_extractor.execute(missing_var_context)

if __name__ == "__main__":
    unittest.main()
