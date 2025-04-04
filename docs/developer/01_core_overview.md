# 多Agent线性工作流框架 - 核心概述

## 1. 目标

设计一个简单、可扩展的基础框架，用于实现线性的多Agent工作流。该框架使用抽象类来定义核心组件（节点），允许用户通过继承这些抽象类来创建具体的工作流节点。框架需要管理节点间的执行顺序和数据（上下文）传递。

包含以下抽象类设计：

- **BaseNode**：所有节点的抽象基类
- **StartNode**：工作流开始节点，处理初始输入
- **LLMNode**：与大语言模型交互的节点，包含上下文处理、提示词模板和输出变量
- **EndNode**：工作流结束节点，处理最终输出
- **Workflow**：工作流执行器，管理节点执行和上下文传递

## 2. 核心概念

* **工作流 (Workflow):** 一个包含有序节点列表的执行单元。它负责按顺序执行节点，并管理整个流程的上下文。
* **节点 (Node):** 工作流中的一个独立执行步骤。每个节点接收输入（来自工作流上下文），执行特定任务，并将输出写回上下文。所有节点都继承自一个基础抽象类 `BaseNode`。
* **工作流上下文 (WorkflowContext):** 一个在工作流执行期间共享的数据容器（例如字典）。节点从中读取输入变量，并将输出变量写入其中。
* **变量 (Variable):** 在工作流上下文中存储的数据单元，通过唯一的名称标识。

## 3. 架构总览

### 工作流上下文 (`WorkflowContext`)

这不需要是一个类，一个简单的Python字典即可满足当前需求。它将在`Workflow`对象内部创建和管理。

* **类型:** `Dict[str, Any]` (一个字符串到任意类型值的映射)
* **职责:** 存储工作流执行过程中的所有变量。

### 节点类层次结构

```
BaseNode (抽象基类)
  ├── StartNode
  ├── LLMNode
  ├── EndNode
  ├── ConditionalBranchNode
  ├── SubWorkflowNode
  └── IterativeWorkflowNode
```

每个节点实现不同的功能，但都遵循相同的接口模式：接收上下文，执行操作，返回更新后的上下文。

### 工作流执行流程

1. 创建各种类型的节点
2. 将节点按执行顺序组装成工作流
3. 准备初始上下文数据
4. 执行工作流 (`workflow.run(initial_context)`)
5. 工作流按顺序执行每个节点，传递和更新上下文
6. 返回最终上下文作为工作流结果

## 4. 实施步骤概览

实施将分为以下步骤进行：

1. **定义基础结构**: 创建 `BaseNode` 抽象类和 `WorkflowContext` 类型别名
2. **实现 StartNode**: 创建工作流的起始节点
3. **实现 EndNode**: 创建工作流的终结节点
4. **实现 LLMNode**: 创建与大语言模型交互的节点
5. **实现 Workflow执行器**: 创建工作流执行逻辑
6. **组装测试工作流**: 使用上述组件创建和测试示例工作流
7. **集成OpenAI客户端**: (可选) 替换测试用客户端为实际的OpenAI API
8. **实现 ConditionalBranchNode**: 创建条件分支节点，支持工作流路径动态选择
9. **实现 SubWorkflowNode**: 创建子工作流节点，支持工作流模块化和复用
10. **实现 IterativeWorkflowNode**: 创建迭代工作流节点，支持循环和迭代处理

每个步骤的详细说明在单独的文档中提供。

## 5. 项目结构
（隐藏了包初始化文件等不必要的文件）
```
smart_education/
├── src/                      # 源代码目录
│   ├── workflow/             # 工作流框架核心
│   │   ├── base.py           # 基础类定义(BaseNode和WorkflowContext)
│   │   ├── engine.py         # 工作流执行器实现
│   │   ├── nodes/            # 各类节点实现
│   │   │   ├── start_node.py # StartNode实现
│   │   │   ├── end_node.py   # EndNode实现
│   │   │   ├── llm_node.py   # LLMNode实现
│   │   │   ├── conditional_branch_node.py # 条件分支节点实现
│   │   │   ├── subworkflow_node.py # 子工作流节点实现
│   │   │   ├── iterative_workflow_node.py # 迭代工作流节点实现
│   │   │   ├── ...          # 其他节点实现
│   │   │   └── custom/       # 自定义节点目录(预留)
│   │   ├── engine.py         # Workflow执行器实现
│   │   └── utils.py          # 工作流通用工具函数
│   └── llm/                  # LLM集成相关
│       ├── base_client.py    # 抽象LLM客户端基类
│       ├── openai_client.py  # OpenAI API客户端
│       └── ...               # 其他LLM客户端实现
├── tests/                    # 测试目录
│   └── ...                   # 各个步骤的单元测试   
├── examples/                 # 示例应用
│   ├── simple_conversation.py # 简单对话工作流示例
│   ├── subworkflow_mood_dialogue.py # 子工作流示例
│   ├── iterative_text_improvement.py # 迭代改进工作流示例
│   ├── ...
│   └── advanced_workflows/   # 高级工作流示例目录
│       └── multi_step_reasoning.py # 多步推理工作流示例
└── docs/                     # 文档目录
    ├── developer/              # 开发者文档
    |   ├── 01_core_overview.md   # 项目概述
    |   ├── 02_step1_...          # 各步骤详细说明
    |   └── 99_future_extensions.md # 未来扩展建议
    └── user/                   # 用户文档

```