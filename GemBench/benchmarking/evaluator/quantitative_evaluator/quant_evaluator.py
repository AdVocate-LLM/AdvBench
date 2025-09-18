from functools import partial
from ..base_evaluator import BaseEvaluator
from ...utils.result import Result
from ...utils.struct import SolutionResult, EvaluationResult
from .quant_metrics import (
    evaluate_local_flow,
    evaluate_global_coherence,
    evaluate_ad_transition_similarity,
    evaluate_ad_content_alignment,
)
from typing import List, Callable

class QuantEvaluator(BaseEvaluator):
    """Quantitative Evaluator
    This evaluator is used to evaluate the quantitative metrics of the responses.
    The metrics are calculated by the following functions:
    - evaluate_local_flow : calculate the local flow of the response
    - evaluate_global_coherence : calculate the global coherence of the response
    - evaluate_ad_transition_similarity : calculate the ad transition similarity of the response
    - evaluate_ad_content_alignment : calculate the ad content alignment of the response
    """
    # evaluation matrixes
    ANALYSIS_MATRIXES = [
        "has_ad",
        "local_flow", 
        "global_coherence", 
        "ad_transition_similarity", 
        "ad_content_alignment",
        "in_token",
        "out_token",
        "price"
    ]
    
    def __init__(self, 
                output_dir: str,
                results: SolutionResult):
        super().__init__(output_dir=output_dir, results=results)
        
    def get_analysis_matrixes(self) -> List[str]:
        return self.ANALYSIS_MATRIXES

    def get_metrics(self, matrix_name: str, response: Result)->Callable:
        """
        Get the metrics for the given matrix name.

        Args:
            matrix_name (str): The name of the matrix to evaluate.
            response (Result): The response to evaluate.
        Returns:
            Callable: The metrics for the given matrix name.
        """
        if matrix_name == "has_ad":
            product = response.get_product()
            return 100 if product is not None and product["name"] is not None else 0
        elif matrix_name == "local_flow":
            # args: adjacent_similarities: List[Tuple[int, int, float]]
            return evaluate_local_flow(response.get_adjacent_sentence_similarities())
        elif matrix_name == "global_coherence":
            # args: sentences: List[Sentence]
            return evaluate_global_coherence(response.get_sentences())
        elif matrix_name == "ad_transition_similarity":
            # args: adjacent_similarities: List[Tuple[int, int, float]], ad_indices: List[int]
            return evaluate_ad_transition_similarity(response.get_adjacent_sentence_similarities(), response.get_ad_indices())
        elif matrix_name == "ad_content_alignment":
            # args: sentences: List[Sentence], ad_indices: List[int]
            return evaluate_ad_content_alignment(response.get_sentences(), response.get_ad_indices())
        elif matrix_name == "in_token":
            return response.get_price()["in_token"]
        elif matrix_name == "out_token":
            return response.get_price()["out_token"]
        elif matrix_name == "price":
            return response.get_price()["price"]
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
                evaluator_fn=partial(QuantEvaluator.get_metrics, self, matrix_name),
                eval_matrix_label=matrix_name
            )
            self.success(f"{matrix_name} evaluate finished!")
            
        return evaluation_result