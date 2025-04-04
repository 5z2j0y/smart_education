from typing import List, Dict, Any, Optional, NamedTuple, Union
import json
from ..base import BaseNode, WorkflowContext
from .json_extractor_node import JSONExtractorNode

# 分类定义数据类
class ClassDefinition(NamedTuple):
    """分类定义数据类"""
    name: str                     # 分类名称
    description: str              # 分类描述
    next_node_id: str             # 下一个节点ID
    examples: Optional[List[str]] = None  # 可选的示例列表

# 分类结果JSON模式
CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "class_name": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reason": {"type": "string"}
    },
    "required": ["class_name"]
}

# 分类提示词模板
CLASSIFICATION_PROMPT_TEMPLATE = """
你是一个专业的问题分类器。请将输入的问题分类到以下类别之一:

{class_definitions}

请以JSON格式返回分类结果，包含以下字段:
- class_name: 选择的分类名称
- confidence: 分类的置信度(0-1之间的小数)
- reason: 简要说明选择该分类的理由

输入问题: {input_text}
"""

class ConditionalBranchNode(BaseNode):
    """
    条件分支节点，基于内容进行分支选择。
    使用LLM将输入内容分类，然后根据分类结果确定下一个节点。
    """
    def __init__(
        self,
        node_id: str,
        node_name: str,
        classes: List[ClassDefinition],
        input_variable_name: str,
        llm_client: Any,
        default_class: Optional[ClassDefinition] = None,
        output_reason: bool = False,
        output_variable_name: str = "classification_result"
    ):
        """
        初始化条件分支节点。

        Args:
            node_id (str): 节点ID。
            node_name (str): 节点名称。
            classes (List[ClassDefinition]): 分类定义列表。
            input_variable_name (str): 输入变量名称，包含待分类的文本。
            llm_client (Any): 用于调用LLM的客户端实例。
            default_class (Optional[ClassDefinition]): 默认分类，当无法确定分类时使用。
            output_reason (bool): 是否将分类原因写入上下文。
            output_variable_name (str): 分类结果将存储在上下文中的变量名称。
        """
        super().__init__(node_id, node_name)
        
        if not classes:
            raise ValueError("Classes list cannot be empty")
        
        self.classes = classes
        self.input_variable_name = input_variable_name
        self.llm_client = llm_client
        self.default_class = default_class
        self.output_reason = output_reason
        self.output_variable_name = output_variable_name
        
        # 创建分类名称到分类定义的映射，方便快速查找
        self.class_map = {cls.name: cls for cls in classes}
        
        # 检查分类名称唯一性
        if len(self.class_map) != len(classes):
            raise ValueError("Class names must be unique")

    def _generate_class_definitions_text(self) -> str:
        """生成分类定义文本，用于LLM提示词"""
        definitions = []
        
        for i, cls in enumerate(self.classes):
            definition = f"{i+1}. {cls.name}: {cls.description}"
            
            # 添加示例（如果有）
            if cls.examples:
                examples_text = ", ".join([f'"{ex}"' for ex in cls.examples])
                definition += f"\n   示例: {examples_text}"
                
            definitions.append(definition)
            
        return "\n\n".join(definitions)

    def _format_classification_prompt(self, input_text: str) -> str:
        """格式化分类提示词"""
        class_definitions = self._generate_class_definitions_text()
        return CLASSIFICATION_PROMPT_TEMPLATE.format(
            class_definitions=class_definitions,
            input_text=input_text
        )

    def _extract_classification(self, llm_response: str) -> Dict[str, Any]:
        """从LLM响应中提取分类结果"""
        # 创建一个临时的JSON提取器
        json_extractor = JSONExtractorNode(
            node_id=f"{self.node_id}_json_extractor",
            node_name="Classification JSON Extractor",
            input_variable_name="llm_response",
            output_variable_name="classification",
            schema=CLASSIFICATION_SCHEMA,
            default_value={
                "class_name": self.default_class.name if self.default_class else "Unknown",
                "confidence": 0,
                "reason": "Failed to extract valid classification"
            },
            raise_on_error=False  # 出错时使用默认值而不是抛出异常
        )
        
        # 提取JSON
        temp_context = {"llm_response": llm_response}
        result_context = json_extractor.execute(temp_context)
        return result_context["classification"]

    def _get_next_node_id(self, class_name: str) -> str:
        """根据分类名称获取下一个节点ID"""
        if class_name in self.class_map:
            return self.class_map[class_name].next_node_id
        elif self.default_class:
            return self.default_class.next_node_id
        else:
            raise ValueError(f"Unknown class '{class_name}' and no default class provided")

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行条件分支节点逻辑。

        Args:
            context (WorkflowContext): 当前工作流上下文。

        Returns:
            WorkflowContext: 更新后的上下文，包含分类结果和下一个节点信息。

        Raises:
            ValueError: 如果输入变量不存在或分类失败且没有默认分类。
        """
        print(f"--- Executing {self} ---")
        print(f"  Input Context: {context}")

        # 检查输入变量是否存在
        if self.input_variable_name not in context:
            raise ValueError(
                f"ConditionalBranchNode '{self.node_id}': Required input variable "
                f"'{self.input_variable_name}' not found in context."
            )

        input_text = context[self.input_variable_name]
        
        # 生成分类提示词
        classification_prompt = self._format_classification_prompt(input_text)
        print(f"  Classification Prompt: {classification_prompt[:100]}...")
        
        try:
            # 调用LLM进行分类
            llm_response = self.llm_client.invoke(classification_prompt)
            print(f"  LLM Response: {llm_response}")
            
            # 提取分类结果
            classification = self._extract_classification(llm_response)
            print(f"  Extracted Classification: {classification}")
            
            # 获取下一个节点ID
            next_node_id = self._get_next_node_id(classification["class_name"])
            print(f"  Next Node ID: {next_node_id}")
            
            # 更新上下文
            updated_context = context.copy()
            
            # 添加分类结果
            updated_context[self.output_variable_name] = classification
            
            # 添加下一个节点ID
            updated_context["next_node_id"] = next_node_id
            
            # 如果需要，添加分类原因
            if self.output_reason and "reason" in classification:
                updated_context[f"{self.output_variable_name}_reason"] = classification["reason"]
            
            print(f"  Output Context: {updated_context}")
            print(f"--- Finished {self} ---")
            
            return updated_context
            
        except Exception as e:
            print(f"  Error in classification: {e}")
            
            # 如果有默认分类，使用它
            if self.default_class:
                print(f"  Using default class: {self.default_class.name}")
                
                # 更新上下文
                updated_context = context.copy()
                updated_context[self.output_variable_name] = {
                    "class_name": self.default_class.name,
                    "confidence": 0,
                    "reason": f"Error occurred: {str(e)}"
                }
                updated_context["next_node_id"] = self.default_class.next_node_id
                
                print(f"  Output Context: {updated_context}")
                print(f"--- Finished {self} ---")
                
                return updated_context
            else:
                # 没有默认分类，抛出异常
                raise ValueError(f"Classification failed and no default class provided: {str(e)}")
