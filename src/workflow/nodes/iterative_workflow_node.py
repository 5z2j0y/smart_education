"""
迭代工作流节点实现，支持重复执行子工作流直到满足条件。
"""
from typing import List, Optional, Dict, Any, Callable, Union, Literal
import json

from ..base import BaseNode, WorkflowContext
from ..engine import Workflow

class IterativeWorkflowNode(BaseNode):
    """
         迭代工作流节点，用于重复执行子工作流直到满足条件。
    
    支持条件控制、最大迭代次数限制、结果累积和中间状态管理，
    适用于需要多轮处理、循环遍历或渐进改进的场景。
    """
    def __init__(
        self,
        node_id: str,
        node_name: str,
        nodes: List[BaseNode],
        condition_function: Callable[[WorkflowContext], bool],
        max_iterations: int = 10,
        input_mapping: Optional[Dict[str, str]] = None,
        output_mapping: Optional[Dict[str, str]] = None,
        iteration_mapping: Optional[Dict[str, str]] = None,
        result_collection_mode: Literal["replace", "append", "merge"] = "replace",
        result_variable: Optional[str] = None,
        next_node_id: Optional[str] = None
    ):
        """
        初始化迭代工作流节点。
        
        Args:
            node_id: 节点唯一标识符
            node_name: 节点描述性名称
            nodes: 子工作流中的节点列表
            condition_function: 判断是否继续迭代的函数，接收当前上下文，返回布尔值
            max_iterations: 最大迭代次数限制
            input_mapping: 主工作流到子工作流的变量映射 {主变量名: 子变量名}
            output_mapping: 子工作流到主工作流的变量映射 {子变量名: 主变量名}
            iteration_mapping: 迭代间的变量传递映射 {当前迭代变量: 下次迭代变量}
            result_collection_mode: 结果收集模式 ("replace"|"append"|"merge")
            result_variable: 存储结果的变量名
            next_node_id: 迭代结束后下一个节点的ID
        """
        super().__init__(node_id, node_name)
        # 存储参数
        self.input_mapping = input_mapping or {}
        self.output_mapping = output_mapping or {}
        self.iteration_mapping = iteration_mapping or {}
        self.next_node_id = next_node_id
        self.condition_function = condition_function
        self.max_iterations = max_iterations
        self.result_collection_mode = result_collection_mode
        self.result_variable = result_variable
        
        # 验证节点列表并创建子工作流
        self._validate_nodes(nodes)
        self.workflow = Workflow(nodes)
        
        # 验证结果收集配置
        self._validate_result_collection()
    
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """执行迭代工作流节点"""
        print(f"--- Executing {self} ---")
        
        # 初始化变量
        iteration_count = 0
        iteration_context = self._prepare_initial_context(context)
        results = []
        final_context = None
        
        # 执行迭代循环
        while self._should_continue(iteration_context, iteration_count):
            print(f"  Starting iteration {iteration_count + 1}")
            
            try:
                # 执行子工作流
                iteration_context = self.workflow.run(iteration_context)
                final_context = iteration_context  # 保存最后一次执行的结果
                
                # 收集结果
                if self.result_variable:
                    # 从输出映射的变量中收集结果
                    for var_name in self.output_mapping.keys():
                        if var_name in iteration_context:
                            result = iteration_context[var_name]
                            self._collect_result(results, result)
                            print(f"  Collected result from variable '{var_name}'")
                            break
                
                # 准备下一次迭代
                iteration_count += 1
                iteration_context["_iteration_count"] = iteration_count
                
                # 应用迭代间变量映射
                if self.iteration_mapping:
                    mapped_context = {}
                    for src_var, dest_var in self.iteration_mapping.items():
                        if src_var in iteration_context:
                            mapped_context[dest_var] = iteration_context[src_var]
                    
                    # 合并其他必要变量
                    for var in iteration_context:
                        if var not in mapped_context and not var.startswith("_"):
                            mapped_context[var] = iteration_context[var]
                    
                    # 保留特殊变量
                    mapped_context["_iteration_count"] = iteration_count
                    
                    iteration_context = mapped_context
                
            except Exception as e:
                print(f"  Iteration {iteration_count + 1} failed: {e}")
                raise RuntimeError(f"IterativeWorkflowNode failed: {e}") from e
        
        print(f"  Completed after {iteration_count} iterations")
        
        # 准备返回上下文
        updated_context = context.copy()
        
        # 应用输出映射
        if final_context:
            for iter_var, main_var in self.output_mapping.items():
                if iter_var in final_context:
                    updated_context[main_var] = final_context[iter_var]
                    print(f"  Mapped output '{iter_var}' to '{main_var}'")
        
        # 添加结果集合
        if self.result_variable and results:
            if self.result_collection_mode == "replace":
                updated_context[self.result_variable] = results[-1]
            elif self.result_collection_mode == "append":
                updated_context[self.result_variable] = results
            elif self.result_collection_mode == "merge" and isinstance(results[-1], dict):
                updated_context[self.result_variable] = results[-1]
        
        # 添加迭代信息
        updated_context["_iterations_completed"] = iteration_count
        
        # 设置下一个节点ID
        if self.next_node_id:
            updated_context["next_node_id"] = self.next_node_id
        
        return updated_context
    
    def _should_continue(self, context: WorkflowContext, iteration_count: int) -> bool:
        """
        判断是否应继续迭代。
        
        Args:
            context: 当前迭代的上下文
            iteration_count: 当前迭代计数
            
        Returns:
            是否应继续迭代
        """
        # 检查最大迭代次数
        if iteration_count >= self.max_iterations:
            print(f"  Reached maximum iterations limit ({self.max_iterations})")
            return False
        
        # 应用用户定义的条件函数
        try:
            should_continue = self.condition_function(context)
            if not should_continue:
                print("  Iteration condition evaluated to False, stopping iterations")
            return should_continue
        except Exception as e:
            print(f"  Error in condition function: {e}")
            # 条件函数出错时默认停止迭代
            return False

    def _prepare_initial_context(self, main_context: WorkflowContext) -> WorkflowContext:
        """
        准备第一次迭代的初始上下文。
        
        Args:
            main_context: 主工作流上下文
            
        Returns:
            初始化后的子工作流上下文
        """
        iteration_context = {}
        
        # 映射输入变量
        for main_var, iter_var in self.input_mapping.items():
            if main_var in main_context:
                iteration_context[iter_var] = main_context[main_var]
            else:
                print(f"  Warning: Input variable '{main_var}' not found in main context")
        
        # 初始化迭代计数
        iteration_context["_iteration_count"] = 0
        
        return iteration_context

    def _prepare_next_iteration(self, current_context: WorkflowContext) -> WorkflowContext:
        """
        准备下一次迭代的上下文。
        
        Args:
            current_context: 当前迭代的上下文
            
        Returns:
            下一次迭代的上下文
        """
        next_context = {}
        
        # 应用迭代间变量映射
        for src_var, dest_var in self.iteration_mapping.items():
            if src_var in current_context:
                next_context[dest_var] = current_context[src_var]
                print(f"  Iteration mapping: '{src_var}' -> '{dest_var}'")
            else:
                print(f"  Warning: Iteration variable '{src_var}' not found for mapping")
        
        # 保留特殊控制变量和其他必要变量
        if "_iteration_count" in current_context:
            next_context["_iteration_count"] = current_context["_iteration_count"]
        
        # 保留未映射但可能在下次迭代中需要的变量
        for var_name in current_context:
            if var_name not in next_context and var_name not in self.iteration_mapping:
                # 跳过已经映射的变量和特殊控制变量
                if not var_name.startswith("_"):
                    next_context[var_name] = current_context[var_name]
        
        return next_context
    
    def _validate_result_collection(self):
        """验证结果收集配置。"""
        valid_modes = ["replace", "append", "merge"]
        if self.result_collection_mode not in valid_modes:
            raise ValueError(f"Invalid result collection mode: {self.result_collection_mode}. Must be one of {valid_modes}")
        
        if self.result_collection_mode in ["append", "merge"] and not self.result_variable:
            raise ValueError(f"Result variable must be specified when using '{self.result_collection_mode}' collection mode")

    def _collect_result(self, results: list, result: Any) -> None:
        """
        根据收集模式处理结果。
        
        Args:
            results: 结果收集列表
            result: 当前迭代的结果
        """
        if self.result_collection_mode == "replace":
            # 清空之前的结果并添加新结果
            results.clear()
            results.append(result)
        elif self.result_collection_mode == "append":
            # 将新结果添加到列表中
            results.append(result)
        elif self.result_collection_mode == "merge" and isinstance(result, dict):
            # 合并字典结果
            merged_result = {}
            # 如果已有结果，取最后一个作为基础
            if results:
                if isinstance(results[-1], dict):
                    merged_result = results[-1].copy()
                else:
                    # 如果最后一个结果不是字典，则退化为append模式
                    results.append(result)
                    return
            # 合并新结果
            merged_result.update(result)
            
            # 更新或添加合并结果
            if results:
                results[-1] = merged_result
            else:
                results.append(merged_result)
        else:
            # 对于不是字典的数据，当使用merge模式时，退化为append
            results.append(result)

    def _map_results_to_main_context(self, main_context: WorkflowContext, 
                                    final_iter_context: WorkflowContext,
                                    collected_results: list) -> WorkflowContext:
        """
        将迭代结果映射回主工作流上下文。
        
        Args:
            main_context: 主工作流上下文
            final_iter_context: 最终迭代的上下文
            collected_results: 收集的结果列表
            
        Returns:
            更新后的主工作流上下文
        """
        updated_context = main_context.copy()
        
        # 映射最终迭代的输出变量
        for iter_var, main_var in self.output_mapping.items():
            if iter_var in final_iter_context:
                updated_context[main_var] = final_iter_context[iter_var]
                print(f"  Mapped '{iter_var}' to '{main_var}': {final_iter_context[iter_var]}")
            else:
                print(f"  Warning: Output variable '{iter_var}' not found in final iteration context")
        
        # 添加收集的结果（如果有）
        if self.result_variable and collected_results:
            if self.result_collection_mode == "replace":
                # 使用最后一个结果
                updated_context[self.result_variable] = collected_results[-1]
            elif self.result_collection_mode == "append":
                # 使用完整的结果列表
                updated_context[self.result_variable] = collected_results
            elif self.result_collection_mode == "merge" and collected_results:
                # 使用合并后的结果
                updated_context[self.result_variable] = collected_results[-1]
        
        # 添加迭代次数信息
        if "_iteration_count" in final_iter_context:
            updated_context["_iterations_completed"] = final_iter_context["_iteration_count"]
        else:
            # 如果没有从迭代上下文拿到迭代计数，使用迭代次数变量
            iterations_completed = len(collected_results) if collected_results else 0
            updated_context["_iterations_completed"] = iterations_completed
        
        # 设置下一个节点ID（如果有）
        if self.next_node_id:
            updated_context["next_node_id"] = self.next_node_id
        
        return updated_context
    
    def _validate_nodes(self, nodes: List[BaseNode]) -> None:
        """
        验证节点列表。
        
        Args:
            nodes: 子工作流节点列表
            
        Raises:
            ValueError: 如果节点列表为空或包含重复ID
        """
        if not nodes:
            raise ValueError("IterativeWorkflowNode requires at least one node")
        
        # 确保节点ID唯一
        node_ids = [node.node_id for node in nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValueError("Duplicate node IDs found in subworkflow nodes")
        
        # 检查节点类型和结构
        from ..nodes.start_node import StartNode
        if not isinstance(nodes[0], StartNode):
            print("  Warning: First node in iterative workflow is not a StartNode")
