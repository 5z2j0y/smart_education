import unittest
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 现在可以导入src模块
from src.workflow.base import BaseNode, WorkflowContext

class TestBaseNode(unittest.TestCase):
    """测试BaseNode抽象基类"""
    
    def test_cannot_instantiate_abstract_class(self):
        """测试无法直接实例化抽象类"""
        with self.assertRaises(TypeError):
            node = BaseNode("test", "Test Node")
    
    def test_can_instantiate_concrete_subclass(self):
        """测试可以实例化具体子类"""
        
        class SimpleNode(BaseNode):
            def execute(self, context: WorkflowContext) -> WorkflowContext:
                return context
        
        # 验证可以创建实例
        node = SimpleNode("simple", "Simple Node")
        self.assertEqual(node.node_id, "simple")
        self.assertEqual(node.node_name, "Simple Node")
        
        # 验证可以执行
        context = {"test": "value"}
        result = node.execute(context)
        self.assertEqual(result, context)
        
        # 验证字符串表示
        self.assertEqual(str(node), "SimpleNode(id='simple', name='Simple Node')")

if __name__ == "__main__":
    unittest.main()
