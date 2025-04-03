# 步骤4: 实现 LLMNode

本步骤我们将实现与大语言模型交互的节点 `LLMNode`，以及用于测试的 `FakeLLMClient`。

## 任务

1. 创建 `FakeLLMClient` 类用于测试，模拟LLM调用
2. 创建 `LLMNode` 类，继承自 `BaseNode`
3. 实现 `__init__`, `_extract_variables_from_template`, `_format_prompt`, 和 `execute` 方法

## 代码实现

首先是测试用的假LLM客户端和真实OpenAI客户端的实现：

```python
# 用于测试的假LLM客户端
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

# 真实的OpenAI客户端实现
from openai import OpenAI

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
```

接下来是LLMNode的实现：

```python
from typing import List, Dict, Any
from string import Template  # 使用Python标准库的Template进行变量替换
from base_node import BaseNode, WorkflowContext  # 假设我们已经在base_node.py中定义了这些

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

## 验证

确保以下验证点通过：

1. **实例化测试**：创建 `FakeLLMClient` 和 `LLMNode` 实例。

    ```python
    # 创建假LLM客户端
    fake_llm = FakeLLMClient()
    
    # 创建LLMNode实例
    llm_node = LLMNode(
        node_id="llm1",
        node_name="Test LLM Node",
        system_prompt_template="Process this text: {input_text}",
        output_variable_name="processed_text",
        llm_client=fake_llm
    )
    
    print(llm_node)  # 应输出: LLMNode(id='llm1', name='Test LLM Node')
    print("需要的输入变量:", llm_node.input_variable_names)  # 应输出: ['input_text']
    ```

2. **变量提取测试**：验证 `_extract_variables_from_template` 方法能正确提取变量名。

    ```python
    # 测试变量提取
    template = "Hello {name}, your age is {age}."
    variables = llm_node._extract_variables_from_template(template)
    print("提取的变量:", variables)  # 应输出包含 'name' 和 'age'
    ```

3. **格式化提示词测试**：验证 `_format_prompt` 方法能正确格式化提示词。

    ```python
    # 测试提示词格式化
    context = {"input_text": "Hello world!"}
    formatted = llm_node._format_prompt(context)
    print("格式化后的提示词:", formatted)  # 应输出: "Process this text: Hello world!"
    ```

4. **执行测试**：调用 `execute` 方法执行节点逻辑。

    ```python
    # 测试完整执行
    context = {"input_text": "Hello world!"}
    result = llm_node.execute(context)
    print("执行结果:", result)
    # 应包含原始输入和LLM响应的新变量: {'input_text': 'Hello world!', 'processed_text': '...'}
    ```

5. **错误处理测试**：提供缺少所需变量的上下文，应该抛出异常。

    ```python
    try:
        # 提供缺少所需变量的上下文
        empty_context = {}
        llm_node.execute(empty_context)
        print("错误：应该抛出异常")
    except ValueError as e:
        print("正确：捕获到变量缺失异常:", e)
    ```

完成这些验证后，`LLMNode` 的实现和假LLM客户端的实现就完成了，可以继续进行下一步。
