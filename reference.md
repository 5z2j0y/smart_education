好的，这是一个基于抽象类的简单线性多Agent工作流框架的设计文档。

## 多Agent线性工作流框架设计文档

### 1. 目标

设计一个简单、可扩展的基础框架，用于实现线性的多Agent工作流。该框架使用抽象类来定义核心组件（节点），允许用户通过继承这些抽象类来创建具体的工作流节点。框架需要管理节点间的执行顺序和数据（上下文）传递。

包含以下抽象类设计：

- BaseNode：所有节点的抽象基类
- StartNode：工作流开始节点，处理初始输入
- LLMNode：与大语言模型交互的节点，包含上下文处理、提示词模板和输出变量
- EndNode：工作流结束节点，处理最终输出
- Workflow：工作流执行器，管理节点执行和上下文传递

### 2. 核心概念

*   **工作流 (Workflow):** 一个包含有序节点列表的执行单元。它负责按顺序执行节点，并管理整个流程的上下文。
*   **节点 (Node):** 工作流中的一个独立执行步骤。每个节点接收输入（来自工作流上下文），执行特定任务，并将输出写回上下文。所有节点都继承自一个基础抽象类 `BaseNode`。
*   **工作流上下文 (WorkflowContext):** 一个在工作流执行期间共享的数据容器（例如字典）。节点从中读取输入变量，并将输出变量写入其中。
*   **变量 (Variable):** 在工作流上下文中存储的数据单元，通过唯一的名称标识。

### 3. 核心组件抽象类设计

我们将使用Python的`abc`模块来定义抽象类和抽象方法。

#### 3.1. 工作流上下文 (`WorkflowContext`)

这不需要是一个类，一个简单的Python字典即可满足当前需求。它将在`Workflow`对象内部创建和管理。

*   **类型:** `Dict[str, Any]` (一个字符串到任意类型值的映射)
*   **职责:** 存储工作流执行过程中的所有变量。

#### 3.2. 基础节点 (`BaseNode`)

所有节点类型的基类，定义了节点的通用接口。

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

# 定义工作流上下文类型别名
WorkflowContext = Dict[str, Any]

class BaseNode(ABC):
    """
    工作流中所有节点的抽象基类。
    """
    def __init__(self, node_id: str, node_name: str):
        """
        初始化基础节点。
        Args:
            node_id (str): 节点的唯一标识符。
            node_name (str): 节点的名称（方便理解）。
        """
        self.node_id = node_id
        self.node_name = node_name

    @abstractmethod
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行节点的核心逻辑。
        该方法必须被子类实现。

        Args:
            context (WorkflowContext): 当前的工作流上下文，包含所有可用变量。

        Returns:
            WorkflowContext: 更新后的工作流上下文。
                 (注意：为简单起见，这里返回更新后的context，
                  也可以设计成直接修改传入的context对象)
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.node_id}', name='{self.node_name}')"

```

#### 3.3. 开始节点 (`StartNode`)

工作流的入口点，负责初始化上下文或载入初始数据。

```python
from typing import List, Dict, Any

class StartNode(BaseNode):
    """
    工作流的开始节点。
    负责将初始输入添加到工作流上下文中。
    """
    def __init__(self, node_id: str, node_name: str, output_variable_names: List[str]):
        """
        初始化开始节点。
        Args:
            node_id (str): 节点ID。
            node_name (str): 节点名称。
            output_variable_names (List[str]): 此节点将创建并添加到上下文中的变量名称列表。
                                             这些变量的值将在工作流启动时提供。
        """
        super().__init__(node_id, node_name)
        self.output_variable_names = output_variable_names

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行开始节点逻辑。
        在此简单实现中，它假设初始值已存在于传入的context中
        （由Workflow执行器在启动时放入）。
        主要职责是验证预期的变量是否存在。

        Args:
            context (WorkflowContext): 包含初始输入的工作流上下文。

        Returns:
            WorkflowContext: 未经修改或已验证的上下文。
        """
        print(f"--- Executing {self} ---")
        print(f"  Input Context: {context}")
        # 验证初始变量是否已由Workflow执行器提供
        for var_name in self.output_variable_names:
            if var_name not in context:
                # 实际应用中可能需要更健壮的错误处理
                raise ValueError(f"StartNode '{self.node_id}': Expected initial variable '{var_name}' not found in context.")
        print(f"  Output Context: {context}")
        print(f"--- Finished {self} ---")
        # 对于StartNode，通常只是传递上下文
        return context
```

#### 3.4. 结束节点 (`EndNode`)

工作流的终点，可能负责整理或提取最终结果。

```python
from typing import List, Dict, Any

class EndNode(BaseNode):
    """
    工作流的结束节点。
    标记工作流执行完毕，并可能提取最终输出变量。
    """
    def __init__(self, node_id: str, node_name: str, input_variable_names: List[str]):
        """
        初始化结束节点。
        Args:
            node_id (str): 节点ID。
            node_name (str): 节点名称。
            input_variable_names (List[str]): 此节点期望从上下文中读取并可能作为最终结果的变量名称列表。
        """
        super().__init__(node_id, node_name)
        self.input_variable_names = input_variable_names

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行结束节点逻辑。
        主要职责是验证所需变量是否存在，并可能提取它们。

        Args:
            context (WorkflowContext): 包含所有执行结果的工作流上下文。

        Returns:
            WorkflowContext: 最终的上下文。
        """
        print(f"--- Executing {self} ---")
        print(f"  Input Context: {context}")
        final_output = {}
        for var_name in self.input_variable_names:
            if var_name not in context:
                raise ValueError(f"EndNode '{self.node_id}': Expected final variable '{var_name}' not found in context.")
            final_output[var_name] = context[var_name]

        print(f"  Final Workflow Variables Extracted: {final_output}")
        print(f"  Output Context: {context}")
        print(f"--- Finished {self} ---")
        # EndNode通常是最后一个节点，返回最终上下文
        return context
```

#### 3.5. LLM 节点 (`LLMNode`)

与大语言模型交互的节点。

```python
from typing import List, Dict, Any
from openai import OpenAI  # 使用OpenAI SDK替代简单的re模块
from string import Template  # 使用Python标准库的Template进行变量替换

# OpenAI客户端实现
class OpenAIClient:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        初始化OpenAI客户端
        Args:
            api_key (str): OpenAI API密钥
            model (str): 要使用的模型名称
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def invoke(self, prompt: str) -> str:
        """
        调用OpenAI API发送请求并获取响应
        Args:
            prompt (str): 发送给模型的提示词
        Returns:
            str: 模型的文本响应
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API调用失败: {e}")
            raise

# 保留用于测试的FakeLLMClient
class FakeLLMClient:
    def invoke(self, prompt: str) -> str:
        print(f"    [Fake LLM] Received prompt: {prompt[:100]}...") # 打印部分提示词
        # 模拟LLM响应
        if "better user's query" in prompt:
            return "A detailed exploration of the concept of youth."
        elif "answer the query in detail" in prompt:
            return "Youth is often defined as the period between childhood and adult age..."
        else:
            return f"LLM Simulation: Processed prompt '{prompt[:50]}...'"

class LLMNode(BaseNode):
    """
    与LLM交互的节点。
    根据输入上下文变量格式化系统提示词，调用LLM，并将结果存入输出变量。
    """
    def __init__(self, node_id: str, node_name: str,
                 system_prompt_template: str,
                 output_variable_name: str,
                 llm_client: Any): # 实际应为 LLMClient 类型
        """
        初始化LLM节点。
        Args:
            node_id (str): 节点ID。
            node_name (str): 节点名称。
            system_prompt_template (str): 包含占位符（如 ${variable_name}）的系统提示词模板。
            output_variable_name (str): LLM响应将存储在上下文中的变量名称。
            llm_client (Any): 用于调用LLM的客户端实例。
        """
        super().__init__(node_id, node_name)
        self.system_prompt_template = system_prompt_template
        self.output_variable_name = output_variable_name
        self.llm_client = llm_client # 实际应用中注入真实的LLM Client
        # 使用Template分析变量名
        self.template = Template(system_prompt_template)
        # 从模板中提取变量名
        self.input_variable_names = self._extract_variables_from_template(system_prompt_template)

    def _extract_variables_from_template(self, template: str) -> List[str]:
        """从模板字符串中提取变量名"""
        # 使用Template.pattern属性提供的正则表达式提取变量名
        # 由于Template使用的是${name}格式，我们需要先将{name}转换为${name}
        template = Template(template.replace("{", "${"))
        # 获取template中的所有变量名
        identifiers = list(set([m[1] for m in Template.pattern.findall(template.template) 
                               if m[1] and m[1].isidentifier()]))
        return identifiers

    def _format_prompt(self, context: WorkflowContext) -> str:
        """使用上下文中的变量值格式化提示词模板。"""
        prompt_data = {}
        for var_name in self.input_variable_names:
            if var_name not in context:
                raise ValueError(f"LLMNode '{self.node_id}': Required variable '{var_name}' not found in context for prompt formatting.")
            prompt_data[var_name] = context[var_name]

        try:
            # 使用标准库的Template进行变量替换
            # 由于Template使用的是${name}格式，而我们的模板使用{name}格式
            # 我们需要将模板中的{name}替换为${name}
            template = Template(self.system_prompt_template.replace("{", "${"))
            formatted_prompt = template.safe_substitute(prompt_data)
            return formatted_prompt
        except KeyError as e:
            raise ValueError(f"LLMNode '{self.node_id}': Error formatting prompt. Missing key: {e}") from e

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """
        执行LLM节点逻辑。
        1. 从上下文中获取所需输入变量。
        2. 格式化系统提示词。
        3. 调用LLM。
        4. 将LLM响应存入上下文。

        Args:
            context (WorkflowContext): 当前工作流上下文。

        Returns:
            WorkflowContext: 包含LLM响应的更新后上下文。
        """
        print(f"--- Executing {self} ---")
        print(f"  Input Context: {context}")

        # 1 & 2. 格式化提示词 (包含检查变量是否存在)
        formatted_prompt = self._format_prompt(context)
        print(f"  Formatted Prompt: {formatted_prompt}")

        # 3. 调用LLM
        try:
            llm_response = self.llm_client.invoke(formatted_prompt)
            print(f"  LLM Response: {llm_response}")
        except Exception as e:
            # 实际应用中应进行更细致的错误处理和重试逻辑
            print(f"  Error calling LLM: {e}")
            raise RuntimeError(f"LLMNode '{self.node_id}' failed during LLM invocation.") from e

        # 4. 更新上下文
        # 创建一个新的context或修改传入的context
        # 为了简单和明确，我们创建一个新的context副本并更新
        updated_context = context.copy()
        updated_context[self.output_variable_name] = llm_response
        print(f"  Output Context: {updated_context}")
        print(f"--- Finished {self} ---")

        return updated_context
```

### 4. 工作流执行器 (`Workflow`)

负责按顺序执行节点列表，并管理上下文传递。

```python
from typing import List, Dict, Any

class Workflow:
    """
    线性工作流执行器。
    """
    def __init__(self, nodes: List[BaseNode]):
        """
        初始化工作流。
        Args:
            nodes (List[BaseNode]): 按执行顺序列出的节点列表。
                                   必须以StartNode开始，以EndNode结束（可选，但推荐）。
        """
        if not nodes:
            raise ValueError("Workflow must contain at least one node.")
        # 可以添加检查确保第一个是StartNode，最后一个是EndNode
        if not isinstance(nodes[0], StartNode):
             print("Warning: Workflow does not start with a StartNode.") # 或抛出错误
        # if not isinstance(nodes[-1], EndNode):
        #     print("Warning: Workflow does not end with an EndNode.") # EndNode非强制

        self.nodes = nodes

    def run(self, initial_context: WorkflowContext) -> WorkflowContext:
        """
        执行整个工作流。
        Args:
            initial_context (WorkflowContext): 工作流启动时的初始数据。
                                                对于StartNode，这里应包含其output_variable_names所需的值。

        Returns:
            WorkflowContext: 工作流执行完毕后的最终上下文。
        """
        print("=== Starting Workflow Execution ===")
        current_context = initial_context.copy() # 使用初始上下文的副本

        for node in self.nodes:
            try:
                # 每个节点执行并返回更新后的上下文
                current_context = node.execute(current_context)
            except Exception as e:
                print(f"!!! Workflow execution failed at node {node} !!!")
                print(f"Error: {e}")
                # 可以选择是停止执行还是记录错误并继续（如果设计允许）
                raise # 重新抛出异常，中断执行

        print("=== Workflow Execution Finished Successfully ===")
        return current_context

```

### 5. 分步骤实施和验证计划

#### 步骤 1: 定义基础结构 (`BaseNode`, `WorkflowContext`)

*   **任务:** 创建 `BaseNode` 抽象类，定义 `__init__` 和抽象方法 `execute`。定义 `WorkflowContext` 类型别名。
*   **代码:** 编写 `BaseNode` 类的代码，如上所示。
*   **验证:**
    *   代码符合Python语法，使用了 `abc.ABC` 和 `abc.abstractmethod`。
    *   尝试实例化 `BaseNode` 会失败（因为它有抽象方法）。
    *   创建一个简单的子类继承 `BaseNode` 并实现 `execute` 方法，验证可以实例化该子类。

#### 步骤 2: 实现 `StartNode`

*   **任务:** 创建 `StartNode` 类，继承自 `BaseNode`，实现其 `__init__` 和 `execute` 方法。
*   **代码:** 编写 `StartNode` 类的代码。`execute` 方法目前可以只打印信息和验证变量（如设计所示）。
*   **验证:**
    *   可以成功创建 `StartNode` 实例。
    *   调用 `start_node.execute({"var1": "value1"})` (假设 `output_variable_names=["var1"]`) 应该能成功执行并通过验证。
    *   调用 `start_node.execute({})` (缺少 `var1`) 应该抛出 `ValueError`。

#### 步骤 3: 实现 `EndNode`

*   **任务:** 创建 `EndNode` 类，继承自 `BaseNode`，实现其 `__init__` 和 `execute` 方法。
*   **代码:** 编写 `EndNode` 类的代码。`execute` 方法主要验证输入变量是否存在于上下文中。
*   **验证:**
    *   可以成功创建 `EndNode` 实例。
    *   调用 `end_node.execute({"result": "final"})` (假设 `input_variable_names=["result"]`) 应该能成功执行并打印提取的变量。
    *   调用 `end_node.execute({})` (缺少 `result`) 应该抛出 `ValueError`。

#### 步骤 4: 实现 `LLMNode` (使用 Fake LLM Client)

*   **任务:** 创建 `LLMNode` 类，继承自 `BaseNode`。实现 `__init__`, `_extract_variables_from_template`, `_format_prompt`, 和 `execute` 方法。创建一个 `FakeLLMClient` 用于测试。
*   **代码:** 编写 `LLMNode` 和 `FakeLLMClient` 的代码。
*   **验证:**
    *   可以成功创建 `LLMNode` 实例，传入 `FakeLLMClient`。
    *   验证 `_extract_variables_from_template` 能正确提取 `{var}` 格式的变量。
    *   调用 `llm_node.execute({"input_var": "some text"})` (假设模板为 `"Process: {input_var}"`，输出变量为 `"output_var"`) 应该：
        *   正确格式化 prompt。
        *   调用 `FakeLLMClient.invoke`。
        *   返回包含 `output_var` 的更新后上下文。
    *   调用 `llm_node.execute({})` (缺少 `input_var`) 应该在 `_format_prompt` 或 `execute` 中抛出 `ValueError`。

#### 步骤 5: 实现 `Workflow` 执行器

*   **任务:** 创建 `Workflow` 类，实现 `__init__` 和 `run` 方法。
*   **代码:** 编写 `Workflow` 类的代码。
*   **验证:**
    *   可以创建 `Workflow` 实例，传入一个节点列表（例如，包含 `StartNode` 和 `EndNode`）。
    *   创建一个简单的两节点工作流 (`StartNode` -> `EndNode`)。
    *   调用 `workflow.run({"initial_data": "hello"})` (假设 `StartNode` 需要 `initial_data`) 应该按顺序执行两个节点的 `execute` 方法，并传递上下文。最终返回 `EndNode` 执行后的上下文。
    *   如果任何节点执行失败（例如，缺少变量），`workflow.run` 应该捕获或抛出异常。

#### 步骤 6: 组装并测试示例工作流

*   **任务:** 使用上面创建的类，构建文档开头描述的示例工作流。
*   **代码:**
    ```python
    # 1. 创建 Fake LLM Client 实例
    fake_llm = FakeLLMClient()

    # 2. 定义节点
    start_node = StartNode(node_id="start", node_name="Start", output_variable_names=["user_query"])
    llm_node_1 = LLMNode(node_id="llm1", node_name="Better Query Generator",
                         system_prompt_template="you need to better user's query. output with bettered user query without other words. here's your input: {user_query}",
                         output_variable_name="better_query",
                         llm_client=fake_llm)
    llm_node_2 = LLMNode(node_id="llm2", node_name="Query Answerer",
                         system_prompt_template="you need to answer the query in detail. here's your input: {better_query}",
                         output_variable_name="llm_answer",
                         llm_client=fake_llm)
    end_node = EndNode(node_id="end", node_name="End", input_variable_names=["llm_answer"]) # 假设最终需要 llm_answer

    # 3. 创建工作流
    workflow = Workflow(nodes=[start_node, llm_node_1, llm_node_2, end_node])

    # 4. 定义初始输入
    initial_input = {"user_query": "what is the youth?"}

    # 5. 运行工作流
    final_context = workflow.run(initial_input)

    # 6. 检查结果
    print("\n=== Final Workflow Context ===")
    print(final_context)
    # 期望 final_context 包含 user_query, better_query, llm_answer
    assert "user_query" in final_context
    assert "better_query" in final_context
    assert "llm_answer" in final_context
    assert final_context["better_query"] == "A detailed exploration of the concept of youth." # 基于 Fake LLM
    assert final_context["llm_answer"] == "Youth is often defined as the period between childhood and adult age..." # 基于 Fake LLM
    ```
*   **验证:** 运行上述代码，观察控制台输出是否符合预期，检查每个节点的执行信息和上下文传递。最终的 `final_context` 是否包含所有预期的变量及其（模拟的）值。

#### 步骤 7: (可选) 集成真实的 OpenAI LLM Client

*   **任务:** 替换 `FakeLLMClient` 为一个基于OpenAI SDK的客户端实现。
*   **代码:** 使用上面定义的 `OpenAIClient` 类，如下所示:
    ```python
    # 创建 OpenAI LLM Client 实例
    openai_client = OpenAIClient(api_key="your-api-key-here", model="gpt-4")
    
    # 定义节点时使用真实的OpenAI客户端
    start_node = StartNode(node_id="start", node_name="Start", output_variable_names=["user_query"])
    llm_node_1 = LLMNode(node_id="llm1", node_name="Better Query Generator",
                         system_prompt_template="you need to better user's query. output with bettered user query without other words. here's your input: {user_query}",
                         output_variable_name="better_query",
                         llm_client=openai_client)
    llm_node_2 = LLMNode(node_id="llm2", node_name="Query Answerer",
                         system_prompt_template="you need to answer the query in detail. here's your input: {better_query}",
                         output_variable_name="llm_answer",
                         llm_client=openai_client)
    end_node = EndNode(node_id="end", node_name="End", input_variable_names=["llm_answer"])
    
    # 其余代码与上面相同
    ```
*   **验证:** 使用真实的OpenAI模型运行示例工作流，确保能正确处理API请求和响应。

### 6. 未来扩展考虑

*   **非线性流程:** 支持条件分支（If/Else Node）、并行执行（Parallel Node）、合并（Join Node）。这需要 `Workflow` 执行器逻辑更复杂，可能需要图结构来表示节点关系。
*   **错误处理与重试:** 在 `BaseNode` 或 `Workflow` 中添加更健壮的错误处理、日志记录和节点重试机制。
*   **节点配置:** 使用配置文件（如YAML, JSON）来定义工作流结构和节点参数，而不是硬编码。
*   **状态持久化:** 在长时间运行或可恢复的工作流中，需要将 `WorkflowContext` 持久化存储。
*   **异步执行:** 对于IO密集型任务（如LLM调用），使用异步IO (`asyncio`) 可以提高效率。所有 `execute` 方法需要变成 `async def execute(...)`。
*   **更复杂的上下文管理:** 可能需要支持变量作用域或更精细的上下文传递控制。
*   **输入/输出模式校验:** 使用 Pydantic 等库来定义和校验节点的输入输出变量类型和结构。

这个设计文档提供了一个清晰的基础框架和实施路径，你可以按照步骤逐步构建和验证你的多Agent工作流系统。