import unittest
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.llm.fake_client import FakeLLMClient
from src.llm.base_client import BaseLLMClient

class TestFakeLLMClient(unittest.TestCase):
    """测试FakeLLMClient的功能"""
    
    def test_initialization(self):
        """测试FakeLLMClient初始化"""
        client = FakeLLMClient()
        self.assertIsInstance(client, BaseLLMClient)
    
    def test_invoke_with_better_query(self):
        """测试调用FakeLLMClient处理优化查询"""
        client = FakeLLMClient()
        response = client.invoke("you need to better user's query. here's your input: what is youth?")
        self.assertEqual(response, "A detailed exploration of the concept of youth.")
    
    def test_invoke_with_answer_query(self):
        """测试调用FakeLLMClient回答查询"""
        client = FakeLLMClient()
        response = client.invoke("you need to answer the query in detail. here's your input: what is youth?")
        self.assertEqual(response, "Youth is often defined as the period between childhood and adult age...")
    
    def test_invoke_with_generic_prompt(self):
        """测试调用FakeLLMClient处理通用提示词"""
        client = FakeLLMClient()
        response = client.invoke("This is a generic prompt")
        self.assertTrue(response.startswith("LLM Simulation: Processed prompt"))

# OpenAIClient的测试需要API密钥，仅做结构示例
# class TestOpenAIClient(unittest.TestCase):
#     """测试OpenAIClient的功能"""
#     
#     def setUp(self):
#         """设置测试环境，需要有效的API密钥"""
#         # 从环境变量或测试配置获取API密钥
#         self.api_key = os.environ.get("OPENAI_API_KEY")
#         if not self.api_key:
#             self.skipTest("OpenAI API密钥未设置")
#         
#         # 创建客户端
#         self.client = OpenAIClient(self.api_key, model="gpt-3.5-turbo")
#     
#     def test_invoke(self):
#         """测试调用OpenAI API，需要网络连接和有效的API密钥"""
#         response = self.client.invoke("Tell me a short joke.")
#         self.assertIsInstance(response, str)
#         self.assertTrue(len(response) > 0)

if __name__ == "__main__":
    unittest.main()
