# 步骤10: 实现 ConditionalBranchNode

本步骤我们将实现条件分支节点 `ConditionalBranchNode`，使工作流支持基于内容的动态分支选择。这个节点将结合LLM的分类能力和JSON提取功能，实现智能路由。

## 核心设计

### 1. ClassDefinition 数据类

```python
from typing import NamedTuple, Optional

class ClassDefinition(NamedTuple):
    """分类定义数据类"""
    name: str                    # 分类名称
    description: str             # 分类描述
    next_node_id: str           # 下一个节点ID
    examples: Optional[list] = None  # 可选的示例列表
```

### 2. 条件分支节点结构

`ConditionalBranchNode` 将包含以下主要组件：

1. **分类器LLM配置**:
   - 专用的提示词模板
   - LLM客户端实例
   - 分类输出格式定义

2. **分类定义管理**:
   - 分类列表：ClassDefinition对象的有序列表
   - 默认分类：未匹配时的兜底路由
   - 分类校验逻辑

3. **内置 JSON 提取**:
   - 集成 JSONExtractorNode 的核心功能
   - 预定义的分类结果模式

4. **错误处理策略**:
   - 提供默认分类选项
   - LLM调用重试机制
   - JSON解析容错处理

## 实现思路

### 1. 节点初始化

```python
class ConditionalBranchNode(BaseNode):
    def __init__(
        self,
        node_id: str,
        node_name: str,
        classes: List[ClassDefinition],
        input_variable_name: str,
        llm_client: Any,
        default_class: Optional[ClassDefinition] = None,
        output_reason: bool = False
    ): 
        """初始化条件分支节点"""
```

### 2. 分类过程

1. **构建分类提示词**:
   - 动态生成包含所有分类定义的提示词
   - 指定JSON输出格式要求
   
2. **获取LLM分类**:
   - 调用LLM进行分类
   - 处理分类响应

3. **提取分类结果**:
   - 解析JSON响应
   - 验证分类有效性

4. **确定下一节点**:
   - 查找匹配的分类定义
   - 返回对应的next_node_id

## 使用示例

```python
# 定义分类
classes = [
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

# 定义默认分类（兜底路由）
default_class = ClassDefinition(
    name="General",
    description="无法明确分类的一般对话",
    next_node_id="general_handler"
)

# 创建条件分支节点
branch_node = ConditionalBranchNode(
    node_id="classifier",
    node_name="Query Classifier",
    classes=classes,
    input_variable_name="user_query",
    llm_client=llm_client,
    default_class=default_class,
    output_reason=True
)

# 提示词模板示例
CLASSIFICATION_PROMPT_TEMPLATE = """
你是一个专业的问题分类器。请将输入的问题分类到以下类别之一:

{class_definitions}

请以JSON格式返回分类结果，包含以下字段:
- class_name: 选择的分类名称
- confidence: 分类的置信度(0-1之间的小数)
- reason: 简要说明选择该分类的理由

输入问题: {input_text}
"""

# 使用内置的JSON提取器处理LLM响应
json_extractor = JSONExtractorNode(
    node_id="json_extract",
    node_name="Classification Extractor",
    input_variable_name="llm_output",
    output_variable_name="classification_result",
    schema=CLASSIFICATION_SCHEMA,
    default_value={
        "class_name": default_class.name,
        "confidence": 0,
        "reason": "Failed to extract valid classification"
    },
    raise_on_error=False  # 提取失败时使用默认值
)
```

## 验证

确保以下验证点通过：

1. **基本分类测试**：

```python
context = {"user_query": "什么是二阶导数?"}
result = branch_node.execute(context)
# 应正确识别为Educational类型并返回对应next_node_id
```

2. **边界条件测试**：

```python
# 测试模糊查询
context = {"user_query": "这道数学题很难"}

# 测试默认分类
context = {"user_query": "..."}  # 不明确的输入

# 测试空输入
context = {"user_query": ""}
```

3. **错误处理测试**：

```python
# 测试LLM调用失败
# 测试JSON解析失败
# 测试无效分类结果
```

4. **集成测试**：

```python
# 创建包含分支的工作流
workflow = Workflow([
    start_node,
    branch_node,
    educational_handler,
    daily_handler,
    end_node
])

# 验证完整的分支路由过程
```

## 实现建议

1. **提示词优化**：
   - 包含清晰的分类标准
   - 提供具体示例
   - 明确输出格式要求

2. **性能考虑**：
   - 缓存常见分类结果
   - 优化JSON提取逻辑
   - 实现异步分类支持

3. **可扩展性**：
   - 支持动态添加/移除分类
   - 允许自定义分类策略
   - 提供分类结果回调

完成这些验证后，条件分支节点将为工作流提供灵活的动态路由能力，显著增强框架的应用场景。
```

## 使用建议

1. **分类定义设计**：
   - 保持分类之间的明确界限
   - 提供充分的示例
   - 设置合理的默认分类

2. **错误处理策略**：
   - 根据业务需求选择默认行为
   - 记录分类结果和理由
   - 实现优雅的降级机制

3. **性能优化**：
   - 控制分类数量
   - 实现结果缓存
   - 考虑批量处理