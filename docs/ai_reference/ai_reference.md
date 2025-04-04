# Smart Education 框架 AI 快速参考

## 节点创建

### StartNode - 工作流起始节点

```python
from src.workflow.nodes.start_node import StartNode

start_node = StartNode(
    node_id="start",                    # 节点唯一标识符
    node_name="Start Node",             # 节点名称(用于日志)
    output_variable_names=["query"],    # 期望在初始上下文中存在的变量列表
    next_node_id=None                   # 可选，指定下一节点ID
)
```

### LLMNode - 大语言模型交互节点

```python
from src.workflow.nodes.llm_node import LLMNode

llm_node = LLMNode(
    node_id="llm",                                     # 节点唯一标识符
    node_name="Query Processor",                       # 节点名称
    system_prompt_template="处理以下问题: {query}",      # 提示词模板，{变量名}会被替换
    output_variable_name="llm_response",               # 输出变量名
    llm_client=llm_client,                             # LLM客户端实例
    stream=False,                                      # 是否使用流式输出
    stream_callback=None,                              # 流式输出回调函数
    next_node_id=None,                                 # 指定下一节点ID
    next_node_selector=None                            # 动态选择下一节点的函数
)
```

### JSONExtractorNode - JSON提取节点

```python
from src.workflow.nodes.json_extractor_node import JSONExtractorNode

json_extractor = JSONExtractorNode(
    node_id="json_extract",                           # 节点唯一标识符
    node_name="JSON Extractor",                       # 节点名称
    input_variable_name="llm_response",               # 输入变量名(含JSON的文本)
    output_variable_name="extracted_data",            # 输出变量名(提取的JSON)
    schema=None,                                      # 可选，JSON Schema用于验证
    default_value={"status": "error"},                # 提取失败时的默认值
    raise_on_error=False                              # 提取失败时是否抛出异常
)
```

### ConditionalBranchNode - 条件分支节点

```python
from src.workflow.nodes.conditional_branch_node import ConditionalBranchNode, ClassDefinition

classes = [
    ClassDefinition(
        name="Positive",                             # 分类名称
        description="积极类别",                       # 分类描述
        next_node_id="positive_handler",             # 匹配时下一节点ID
        examples=["很好", "喜欢", "满意"]             # 示例，帮助分类
    ),
    ClassDefinition(
        name="Negative",
        description="消极类别",
        next_node_id="negative_handler",
        examples=["不好", "不喜欢", "不满意"]
    )
]

default_class = ClassDefinition(                     # 默认分类(可选)
    name="Neutral", 
    description="默认类别",
    next_node_id="neutral_handler"
)

branch_node = ConditionalBranchNode(
    node_id="branch",                                # 节点唯一标识符
    node_name="Conditional Branch",                  # 节点名称
    classes=classes,                                 # 分类定义列表
    input_variable_name="text",                      # 输入变量名(待分类文本)
    llm_client=llm_client,                           # LLM客户端实例
    default_class=default_class,                     # 默认分类
    output_reason=True                               # 是否输出分类原因
)
```

### SubWorkflowNode - 子工作流节点

```python
from src.workflow.nodes.subworkflow_node import SubWorkflowNode

sub_workflow = SubWorkflowNode(
    node_id="sub_workflow",                          # 节点唯一标识符
    node_name="Sub Workflow",                        # 节点名称
    nodes=[node1, node2, node3],                     # 子工作流节点列表
    input_mapping={"main_var": "sub_var"},           # 主->子变量映射
    output_mapping={"sub_result": "main_result"},    # 子->主变量映射
    entry_node_id=None,                              # 可选，子工作流入口节点ID
    exit_node_id=None,                               # 可选，子工作流出口节点ID
    next_node_id=None                                # 可选，子工作流结束后的下一节点ID
)
```

### IterativeWorkflowNode - 迭代工作流节点

```python
from src.workflow.nodes.iterative_workflow_node import IterativeWorkflowNode

# 定义迭代条件函数
def condition_func(context):
    # 当分数小于0.8时继续迭代
    score = context.get("evaluation", {}).get("score", 0)
    return score < 0.8 and context.get("_iteration_count", 0) < 5

iterative_node = IterativeWorkflowNode(
    node_id="iterative",                             # 节点唯一标识符
    node_name="Iterative Workflow",                  # 节点名称
    nodes=[node1, node2, node3],                     # 迭代工作流节点列表
    condition_function=condition_func,               # 迭代条件函数
    max_iterations=10,                               # 最大迭代次数
    input_mapping={"initial": "current"},            # 主->迭代变量映射
    output_mapping={"final": "result"},              # 迭代->主变量映射
    iteration_mapping={"improved": "current"},       # 迭代间变量映射
    result_collection_mode="append",                 # 结果收集模式: replace/append/merge
    result_variable="history",                       # 存储结果的变量名
    next_node_id=None                                # 可选，迭代结束后的下一节点ID
)
```

### EndNode - 工作流结束节点

```python
from src.workflow.nodes.end_node import EndNode

end_node = EndNode(
    node_id="end",                                   # 节点唯一标识符
    node_name="End Node",                            # 节点名称
    input_variable_names=["result", "metadata"]      # 从上下文中提取的结果变量列表
)
```

## 工作流创建与执行

### 创建工作流

```python
from src.workflow.engine import Workflow

workflow = Workflow([
    start_node,
    llm_node,
    branch_node,
    positive_handler,
    negative_handler,
    end_node
])
```

### 执行工作流

```python
# 创建初始上下文
context = {
    "query": "用户输入的问题",
    "metadata": {"source": "user_interface"}
}

# 执行工作流
try:
    final_context = workflow.run(context)
    
    # 处理结果
    result = final_context.get("result")
    print(f"工作流执行结果: {result}")
except Exception as e:
    print(f"工作流执行失败: {e}")
```

## LLM客户端

### 创建DeepSeek客户端

```python
from src.llm.deepseek_client import DeepSeekClient

# 从环境变量获取API密钥
api_key = os.environ.get("DEEPSEEK_API_KEY")

# 创建DeepSeek客户端
deepseek_llm = DeepSeekClient(
    api_key=api_key,              # API密钥
    model="deepseek-chat",        # 模型名称
    temperature=0.7,              # 温度参数(可选)
    max_tokens=2000               # 最大输出tokens(可选)
)
```

### 创建测试客户端

```python
from src.llm.fake_client import FakeLLMClient

# 创建测试客户端
fake_llm = FakeLLMClient()

# 设置预定义回复
fake_llm.set_response_sequence([
    "第一个回复",
    "第二个回复",
    '{"key": "value", "score": 0.9}'  # 也可以预设JSON
])
```

## 常见模式与最佳实践

### 流式输出处理

```python
def stream_callback(text_chunk):
    """处理流式输出的文本片段"""
    print(text_chunk, end="", flush=True)

# 创建支持流式输出的LLM节点
stream_node = LLMNode(
    # ...基本参数...
    stream=True,
    stream_callback=stream_callback
)
```

### JSON处理模式

```python
# LLM生成JSON
json_generator = LLMNode(
    # ...基本参数...
    system_prompt_template="以JSON格式回答: {query}",
    output_variable_name="json_text"
)

# 提取和验证JSON
json_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "score": {"type": "number"}
    },
    "required": ["name", "score"]
}

json_extractor = JSONExtractorNode(
    # ...基本参数...
    input_variable_name="json_text",
    output_variable_name="validated_json",
    schema=json_schema
)
```

### 迭代改进模式

```python
# 定义迭代条件：质量评分低于阈值时继续迭代
def quality_check(context, threshold=0.8):
    if "evaluation" not in context:
        return True
    try:
        eval_data = context["evaluation"]
        if isinstance(eval_data, str):
            import json
            eval_data = json.loads(eval_data)
        quality_score = eval_data.get("quality_score", 0)
        return quality_score < threshold
    except:
        return False

# 创建迭代节点
improvement_node = IterativeWorkflowNode(
    # ...基本参数...
    condition_function=lambda ctx: quality_check(ctx, 0.8),
    iteration_mapping={"improved_text": "input_text"},
    result_collection_mode="append",
    result_variable="improvement_history"
)
```
