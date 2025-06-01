import re
import random
from .base_agent import BaseAgent
from ..prompts.compare_prompt import SYS_EVAL_JUDGE_MT, USER_EVAL_JUDGE_MT
from ..tools.export2csv import Export2CSV
from benchmarking.utils.struct import SolutionResult, EvaluationResult
from typing import List, Tuple
import os

class CompareAgent(BaseAgent):
    """Class for comparing responses using LLM as a judge"""
    
    def __init__(self, judge_agent: str = 'gpt-4o'):
        """Initialize the evaluator with specified models
        
        Args:
            judge_agent: Model used for evaluation
        """
        super().__init__(judge_agent)
        self.system_prompt = SYS_EVAL_JUDGE_MT

    def _extract_judge(self, stripped: str):
        """Extract judge decision from response
        
        Args:
            stripped: The stripped response
        Returns:
            int: The judge decision
        
        For example:(Because our prompt is designed to use A, B, C to represent the control and competitor, so the output is always 1, -1, 0)
        If the response is "The answer is [[A]]", the output should be 1.
        If the response is "The answer is [[B]]", the output should be -1.
        If the response is "The answer is [[C]]", the output should be 0.
        """
        pattern = r'\[\[([ABC])\]\]'
        matches = re.findall(pattern, stripped)
        if matches:
            value = matches[-1] 
            if value == 'A':
                return 1  # control better
            elif value == 'B':
                return -1  # competitor better
            elif value == 'C':
                return 0  # same
        return None
    
    def _format_judge_result_to_emoji(self, extracted_num: List[int]) -> Tuple[List[str], List[str], List[str]]:
        """Format the judge result to emoji
        
        Args:
            extracted_num: List[int]
        Returns:
            Tuple[List[str], List[str], List[str]]: The judge result to emoji
        
        For example, if the judge result is [1, -1, 0], the output should be:
        (
            ["✅","❌","❌"],
            ["❌","✅","❌"],
            ["❌","❌","✅"]
        )
        """
        return (
            [
                "✅" if num == 1 else "❌" for num in extracted_num
            ],
            [
                "✅" if num == -1 else "❌" for num in extracted_num
            ],
            [
                "✅" if num == 0 else "❌" for num in extracted_num
            ]
        )
    
    def _calculate_score(self, extracted_num: List[int]) -> Tuple[float, float, float]:
        """Calculate the score of the judge result
        
        Args:
            extracted_num: List[int]
        Returns:
            Tuple[float, float, float]: The score of the judge result -> (A better, B better, same) under 0-100 scale
        """
        A_better = 0
        B_better = 0
        same = 0
        for num in extracted_num:
            if num == 1:
                A_better += 1
            elif num == -1:
                B_better += 1
            else:
                same += 1
        return (A_better / len(extracted_num) * 100, B_better / len(extracted_num) * 100, same / len(extracted_num) * 100)
    
    def compare_A_B_solutions(self, 
                            A_Solutions: SolutionResult, 
                            B_Solutions: SolutionResult,
                            export_path: str = None
                            ) -> EvaluationResult:
        """Compare the A and B solutions
        
        Args:
            A_Solutions: SolutionResult
            B_Solutions: SolutionResult
            export_path: str
        Returns:
            EvaluationResult: The result of the comparison        
        """
        evaluation_result = EvaluationResult()
        
        # Convert SolutionResult to matrices
        a_solution_matrices= A_Solutions._to_matrix()
        b_solution_matrices= B_Solutions._to_matrix()
        
        for a_solution, b_solution in zip(a_solution_matrices, b_solution_matrices):
            if a_solution[3] != b_solution[3]:
                assert "The solution matrices pairs matching error"
        
        questions = [matrix[3] for matrix in a_solution_matrices]
        a_answers = [matrix[6] for matrix in a_solution_matrices]
        b_answers = [matrix[6] for matrix in b_solution_matrices]
        
        # Randomly swap A and B in 50% of cases for fairer evaluation
        swapped = []
        format_questions = []
        for question, a_answer, b_answer in zip(questions, a_answers, b_answers):
            swap = random.random() < 0.5
            swapped.append(swap)
            
            if swap:
                # Swap A and B positions
                format_questions.append(USER_EVAL_JUDGE_MT.format(
                    question=question,
                    answer_a=b_answer,  # B in A position
                    answer_b=a_answer   # A in B position
                ))
            else:
                # Keep original order
                format_questions.append(USER_EVAL_JUDGE_MT.format(
                    question=question,
                    answer_a=a_answer,
                    answer_b=b_answer
                ))
        
        responses = self.answer_multiple(format_questions)
        
        # Extract and adjust scores based on swapping
        raw_scores = [self._extract_judge(response) for response in responses]
        scores = []
        for raw_score, was_swapped in zip(raw_scores, swapped):
            if was_swapped and raw_score is not None:
                # Reverse the score if positions were swapped
                if raw_score == 1:
                    scores.append(-1)  # A was better but in B position
                elif raw_score == -1:
                    scores.append(1)   # B was better but in A position
                else:
                    scores.append(0)   # Same remains same
            else:
                scores.append(raw_score)
        
        A_better_score, B_better_score, same_score = self._calculate_score(scores)
        # if export_path is not None, export the result to CSV file
        if export_path is not None:
            emoji_A, emoji_B, emoji_same = self._format_judge_result_to_emoji(scores)
            # Format swapped status
            swapped_status = ["Yes" if swap else "No" for swap in swapped]
            Export2CSV(columns=[
                        'Question', 
                        A_Solutions.get_keys_by_attr('solution_name')[0], 
                        B_Solutions.get_keys_by_attr('solution_name')[0], 
                        'Response', 
                        'Judge Result',
                        'Swapped',
                        f"{A_Solutions.get_keys_by_attr('solution_name')[0]} better ({A_better_score:.2f}%)",
                        f"{B_Solutions.get_keys_by_attr('solution_name')[0]} better ({B_better_score:.2f}%)",
                        f"same ({same_score:.2f}%)"
                    ], 
                    data=zip(questions, a_answers, b_answers, responses, scores, swapped_status, emoji_A, emoji_B, emoji_same), 
                    export_path=os.path.join(export_path,f"{A_Solutions.get_keys_by_attr('solution_name')[0]}_vs_{B_Solutions.get_keys_by_attr('solution_name')[0]}.xlsx")
            ).export2csv()
        
        for a_answer, b_answer, score in zip(a_solution_matrices, b_solution_matrices, scores):
            # 0: solution_name
            # 1: data_set
            # 2: repeat_id
            # 3: prompt
            # 4: category
            # 5: tag
            # 6: raw_answer
            # 7: product
            a_name = a_answer[5]
            b_name = b_answer[5]
            solution_name = f"{a_name} vs {b_name}"
            dataset = a_answer[1]
            repeat_id = a_answer[2]
            category = a_answer[4]

            comparisons = [
                ("better", score == 1),
                ("worse", score == -1),
                ("same", score == 0),
            ]

            for matrix, is_true in comparisons:
                evaluation_result.add_result(
                    solution_name=solution_name,
                    dataSet=dataset,
                    repeat_id=repeat_id,
                    analysis_matrix=matrix,
                    category=category,
                    result=100 if is_true else 0
                )                
            
        return evaluation_result
