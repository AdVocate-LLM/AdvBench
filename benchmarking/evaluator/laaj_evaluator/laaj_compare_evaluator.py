from benchmarking.evaluator.base_evaluator import BaseEvaluator
from benchmarking.evaluator.laaj_evaluator.agents.compare_agent import CompareAgent
from benchmarking.utils.struct import SolutionResult, EvaluationResult
from typing import List, Any


class CompareEvaluator(BaseEvaluator):
    """Compare Evaluator
    This evaluator is used to compare the results of the competitor and the control.
    The result is a list of tuples, each tuple contains a question, a_answer, b_answer, and a judge result.
    The judge result is 1 if the control is better, -1 if the competitor is better, and 0 if they are the same.
    """
    ANALYSIS_MATRIXES = [
        "compare_result"
    ]
    
    def __init__(self, 
                output_dir: str,
                results: SolutionResult,
                judge_model: str='gpt-4o'                
                ):
        super().__init__(output_dir=output_dir, results=results)
        self.compare_judge = CompareAgent(judge_model)
        
    def get_analysis_matrixes(self) -> List[str]:
        return self.ANALYSIS_MATRIXES
    
    def get_matrices(self, matrix_name: str, records: Any, is_saved: bool = True) -> EvaluationResult:
        """
        Get the analysis matrixes result.
        
        Args:
        - matrix_name (str): The name of the analysis matrixes.
        - records (Any): The records of the analysis matrixes.
        - is_saved (bool): Whether to save the result.
            
        Returns:
            EvaluationResult: The result of the analysis matrixes.
        
        For example:
        {
            "solution_name_A_better than solution_name_B": 0.95,
            "solution_name_B_better than solution_name_A": 0.01,
            "solution_name_A same as solution_name_B": 0.04
        }
        """
        if matrix_name == "compare_result":
            if (isinstance(records, tuple) and 
                len(records) == 2 and 
                isinstance(records[0], SolutionResult) and 
                isinstance(records[1], SolutionResult)):
                # get questions, a_answers, b_answers from response
                compare_result = self.compare_judge.compare_A_B_solutions(
                    A_Solutions=records[0],
                    B_Solutions=records[1],
                    export_path=self.output_dir if is_saved else None
                )
                return compare_result
            else:
                raise ValueError(f"Invalid response type: {type(records)}")
        else:
            raise ValueError(f"Invalid matrix name: {matrix_name}")
    
    def evaluate(self, analysis_matrixes: List[str]=None, is_saved: bool = True) -> EvaluationResult:
        """
        Evaluate the result.
        
        Args:
        - analysis_matrixes (List[str]): The analysis matrixes to evaluate.
        - is_saved (bool): Whether to save the result.
            
        Returns:
            Dict[str, Dict[str, Dict[str, float]]]: The evaluated result grouped by dimension (solution_name and repeat_id...)
        For example:
        {
            "data_set_1":{
                "solution_A vs solution_B":{
                    "solution_name_A_better than solution_name_B": 0.95,
                    "solution_name_B_better than solution_name_A": 0.01,
                    "solution_name_A same as solution_name_B": 0.04
                },
                "solution_A vs solution_C":{
                    "solution_name_A_better than solution_name_C": 0.95,
                    "solution_name_C_better than solution_name_A": 0.01,
                    "solution_name_A same as solution_name_C": 0.04
                },
                ...
            },
            "data_set_2":{
                ...
            },
            "__all__":{
                ...
            }
        }
        """        
        evaluation_result = EvaluationResult()
        
        if analysis_matrixes is None:
            analysis_matrixes = self.ANALYSIS_MATRIXES
        
        # self.stage("Compare Evaluation Start...")
        # Evaluate the all the pairs of solutions combinations
        # compare pair by pair
        result_group_by_solution = self.results.group_by_attrs(attrs=["solution_name"])
        # compare each solution with the others
        all_of_compare_groups = []
        
        for solution_i in result_group_by_solution.items():
            for solution_j in result_group_by_solution.items():
                if solution_i != solution_j and (solution_j, solution_i) not in all_of_compare_groups:
                    all_of_compare_groups.append((solution_i, solution_j))
        
        # compare the solutions in the compare groups
        for compare_group in all_of_compare_groups:
            self.section(f"Compare {compare_group[0][0][0]} and {compare_group[1][0][0]}")
            solution_i = compare_group[0]
            solution_j = compare_group[1]

            # compare the results
            compare_result = self.get_matrices(
                matrix_name="compare_result", 
                records=(solution_i[1], solution_j[1]), 
                is_saved=is_saved
            )
            
            evaluation_result += compare_result
        
        return evaluation_result
