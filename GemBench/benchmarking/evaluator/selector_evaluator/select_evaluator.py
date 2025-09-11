from functools import partial
from ..base_evaluator import BaseEvaluator
from ...utils.result import Result
from ...utils.struct import SolutionResult, EvaluationResult
from typing import List, Callable, Dict
from ...dataset import GemDatasets

class SelectEvaluator(BaseEvaluator):
    """Selector Evaluator
    This evaluator is used to evaluate the selector.
    The metrics are calculated by the following functions:
    - product_selection_accuracy : calculate the accuracy of the product selection
    """
    # evaluation matrixes
    ANALYSIS_MATRIXES = [
        "product_selection_accuracy"
    ]
    
    def __init__(self, 
                output_dir: str,
                best_product_selectors: Dict[str, Callable],
                results: SolutionResult = None):
        super().__init__(output_dir=output_dir, results=results)
        self.best_product_selectors = best_product_selectors
        # Initialize dataset
        self.dataset = GemDatasets()
        
    def get_analysis_matrixes(self) -> List[str]:
        return self.ANALYSIS_MATRIXES

    def get_metrics(self, matrix_name: str, response: Result) -> float:
        """
        Get the metrics for the given matrix name.

        Args:
            matrix_name (str): The name of the matrix to evaluate.
            response (Result): The response to evaluate.
        Returns:
            float: The metrics for the given matrix name.
        """
        if matrix_name == "product_selection_accuracy":
            score = self.dataset.get_score_by_query_selection(
                    query=response.get_prompt(), 
                    selection=response.get_product()
                )
            return score
        else:
            raise ValueError(f"Invalid matrix name: {matrix_name}")
    
    def evaluate(self, eval_matrix_list: List[str]) -> EvaluationResult:
        """
        Evaluate all responses for the given matrix list.
        
        Args:
            eval_matrix_list (List[str]): The list of matrix names to evaluate.
        Returns:
            EvaluationResult: The result of the evaluation.
        """
        # self.stage("Quantitative Evaluation Start...")
        evaluation_result = EvaluationResult()
        for matrix_name in eval_matrix_list:
            self.section(f"Evaluating {matrix_name}...")
            evaluation_result += self.results.self_evaluated_with_matrix_by_fn(
                evaluator_fn=partial(SelectEvaluator.get_metrics, self, matrix_name),
                eval_matrix_label=matrix_name
            )
            self.success(f"{matrix_name} evaluate finished!")
            
        return evaluation_result