# 快速上手智能教育多Agent框架

本文档将指导您快速上手智能教育多Agent框架，学习如何创建LLM节点和工作流。通过本指南，您将了解框架的基本概念，并能够构建自己的智能工作流。

## 目录

1. [框架概述](#1-框架概述)
2. [安装与配置](#2-安装与配置)
3. [基本概念](#3-基本概念)
4. [创建LLM节点](#4-创建llm节点)
5. [构建工作流](#5-构建工作流)
6. [运行与测试](#6-运行与测试)
7. [进阶使用](#7-进阶使用)
8. [常见问题](#8-常见问题)

---

## 1. 框架概述

智能教育多Agent框架是一个简单而强大的工具，用于构建基于LLM（大型语言模型）的工作流。它提供了一种模块化的方式来设计和执行由多个节点组成的处理流程，每个节点可以执行特定的任务，如与LLM交互、处理输入/输出等。

**主要特点：**
- 简单直观的API设计
- 模块化节点系统
- 灵活的上下文管理
- 支持多种LLM客户端
- 可扩展的架构

---

## 2. 安装与配置

### 2.1 安装框架

目前，您可以通过克隆GitHub仓库来使用该框架：

```bash
git clone https://github.com/yourusername/smart_education.git
cd smart_education
```

### 2.2 环境配置

为确保所有依赖项正确安装，请运行：

```bash
pip install -r requirements.txt
```

### 2.3 配置LLM API

如果您计划使用OpenAI或DeepSeek等LLM服务，需要在环境变量中设置相应的API密钥：

**对于Windows：**
```cmd
set OPENAI_API_KEY=your_api_key_here
```

**对于Linux或macOS：**
```bash
export OPENAI_API_KEY=your_api_key_here
```

---

## 3. 基本概念

在开始创建节点和工作流之前，了解以下核心概念非常重要：

### 3.1 工作流上下文 (WorkflowContext)

工作流上下文是一个字典，用于在节点之间传递数据。它包含所有输入、中间结果和输出变量。

### 3.2 节点 (Node)

节点是工作流的基本构建块。每个节点接收上下文，执行特定操作，然后返回更新后的上下文。框架提供了几种基本节点类型：

- **StartNode**: 工作流的入口点，验证初始输入。
- **LLMNode**: 与语言模型交互的节点。
- **EndNode**: 工作流的终点，提取最终结果。
- **ConditionalBranchNode**: 条件分支节点，基于内容分类确定工作流执行路径。

### 3.3 工作流 (Workflow)

工作流是一系列按顺序执行的节点。它管理上下文的传递和节点的执行流程。

---

## 4. 创建LLM节点

LLM节点是与大语言模型交互的核心组件。下面是创建LLM节点的步骤：

### 4.1 创建LLM客户端实例

```python
from src.llm.openai_client import OpenAIClient
from src.llm.fake_client import FakeLLMClient  # 用于测试

# 生产环境：使用真实的OpenAI客户端
api_key = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAIClient(api_key=api_key, model="gpt-3.5-turbo")

# 开发/测试环境：使用假客户端
fake_client = FakeLLMClient()
```

### 4.2 创建LLM节点

```python
from src.workflow.nodes.llm_node import LLMNode

# 创建一个简单的LLM节点
query_improver = LLMNode(
    node_id="query_improver",  # 唯一标识符
    node_name="Query Improver",  # 描述性名称
    system_prompt_template="优化以下查询，使其更清晰：{user_query}",  # 提示词模板
    output_variable_name="improved_query",  # 输出变量名
    llm_client=openai_client  # LLM客户端实例
)
```

#### 提示词模板

提示词模板支持使用`{变量名}`格式引用上下文中的变量。例如：

```python
template = "用户查询：{query}，用户偏好：{preferences}"
```

#### 流式输出

```python
# 定义流式输出的回调函数
def stream_callback(text_chunk):
    print(text_chunk, end="", flush=True)

# 创建支持流式输出的LLM节点
streaming_node = LLMNode(
    node_id="streaming_llm",
    node_name="Streaming LLM Node",
    system_prompt_template="详细回答：{question}",
    output_variable_name="streaming_answer",
    llm_client=openai_client,
    stream=True,  # 启用流式输出
    stream_callback=stream_callback  # 设置回调函数
)
```

---

## 5. 构建工作流

### 5.1 创建所有必要的节点

```python
from src.workflow.nodes.start_node import StartNode
from src.workflow.nodes.end_node import EndNode

# 创建起始节点
start_node = StartNode(
    node_id="start",
    node_name="Start Node",
    output_variable_names=["user_query"]  # 期望在初始上下文中存在的变量
)

# 创建LLM节点
llm_node = LLMNode(
    node_id="llm",
    node_name="Query Processor",
    system_prompt_template="回答以下问题：{user_query}",
    output_variable_name="llm_answer",
    llm_client=openai_client
)

# 创建结束节点
end_node = EndNode(
    node_id="end",
    node_name="End Node",
    input_variable_names=["llm_answer"]  # 从最终上下文中提取的变量
)
```

### 5.2 组装工作流

```python
from src.workflow.engine import Workflow

# 创建工作流
workflow = Workflow(nodes=[start_node, llm_node, end_node])
```

### 5.3 准备初始上下文

```python
# 创建初始上下文
initial_context = {
    "user_query": "什么是人工智能？"
}
```

---

## 6. 运行与测试

```python
try:
    # 运行工作流
    final_context = workflow.run(initial_context)
    
    # 输出结果
    print("\n=== 工作流执行结果 ===")
    print(f"用户查询: {final_context['user_query']}")
    print(f"LLM回答: {final_context['llm_answer']}")
    
except Exception as e:
    print(f"工作流执行失败: {e}")
```

---

## 7. 进阶使用

### 7.1 自定义节点

```python
from src.workflow.base import BaseNode, WorkflowContext

class MyCustomNode(BaseNode):
    def __init__(self, node_id, node_name, input_var, output_var):
        super().__init__(node_id, node_name)
        self.input_var = input_var
        self.output_var = output_var
    
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        # 检查输入变量是否存在
        if self.input_var not in context:
            raise ValueError(f"Required variable '{self.input_var}' not found")
        
        # 处理数据
        input_data = context[self.input_var]
        result = self._process_data(input_data)
        
        # 更新上下文
        updated_context = context.copy()
        updated_context[self.output_var] = result
        return updated_context
    
    def _process_data(self, data):
        # 实现您的自定义逻辑
        return data.upper()  # 示例：转换为大写
```

### 7.2 条件分支工作流

框架支持基于内容的动态分支，您可以创建条件分支节点来实现更复杂的决策逻辑：

```python
from src.workflow.nodes.conditional_branch_node import ConditionalBranchNode, ClassDefinition

# 定义分类类别
classes = [
    ClassDefinition(
        name="Educational",  # 分类名称
        description="教育相关的提问或陈述",  # 分类描述
        next_node_id="educational_handler",  # 匹配此分类时下一个要执行的节点ID
        examples=["什么是微积分?", "如何学好英语?"]  # 可选的示例列表
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
    classes=classes,  # 分类列表
    input_variable_name="user_query",  # 输入变量
    llm_client=llm_client,  # 用于分类的LLM客户端
    default_class=default_class,  # 默认分类（可选）
    output_reason=True  # 是否输出分类原因（可选）
)
```

#### 组装分支工作流

条件分支工作流需要为每个分支定义处理节点，并将它们组装成一个完整的工作流：

```python
# 创建工作流，包含所有可能路径的节点
workflow = Workflow([
    start_node,
    branch_node,
    educational_node,  # 教育分类的处理节点
    daily_node,        # 日常分类的处理节点
    general_node,      # 默认分类的处理节点
    educational_end,   # 教育分支的结束节点
    daily_end,         # 日常分支的结束节点
    general_end        # 默认分支的结束节点
])

# 执行工作流时，框架将根据分类结果自动选择分支
final_context = workflow.run(initial_context)

# 分类结果保存在上下文中
classification = final_context["classification_result"]
print(f"分类: {classification['class_name']}")
print(f"置信度: {classification.get('confidence', 'N/A')}")
```

条件分支节点使用LLM对输入内容进行分类，然后根据分类结果将执行流程引导到对应的处理节点。这使您能够创建动态响应不同类型输入的智能工作流。

---

## 8. 常见问题

### Q: 如何处理LLM API调用错误？

```python
try:
    result = workflow.run(initial_context)
except Exception as e:
    print(f"工作流执行失败: {e}")
    # 实施错误恢复策略
```

### Q: 如何在不同节点间共享大型数据？

对于大型数据，建议在上下文中存储引用而不是数据本身，例如文件路径或数据库ID。

### Q: 框架是否支持并行执行节点？

当前版本仅支持线性工作流（节点按顺序执行）。并行执行是计划中的未来扩展功能。

### Q: 如何在一个工作流中实现多条执行路径？

使用`ConditionalBranchNode`可以创建基于内容的动态分支。参考[条件分支工作流](#72-条件分支工作流)部分了解详细用法。

---

恭喜！您现在已经了解了智能教育多Agent框架的基础知识，并且能够创建自己的LLM节点和工作流。随着您对框架的深入了解，可以构建更复杂、更强大的应用。

如有更多问题，请参考项目文档或提交GitHub issue。

祝您使用愉快！