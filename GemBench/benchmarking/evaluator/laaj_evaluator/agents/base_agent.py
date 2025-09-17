from ....utils.oracle import Oracle
from ....utils.struct import SolutionResult
from ..tools.export2csv import Export2CSV
from typing import List, Tuple, Any
from ....utils.logger import ModernLogger
import os

class BaseAgent(ModernLogger):
    def __init__(self, model:str):
        super().__init__()
        self.model = Oracle(model)
        self.system_prompt = ''
        
    def answer(self, question:str) -> str:
        response = self.model.query(self.system_prompt, question)
        if response.startswith('QUERY_FAILED:'):
            self.error(f"Query failed for model {self.model.model_name} with error: {response}")
        return response
    
    def answer_multiple(self, questions:List[str]) -> List[str]:
        responses = self.model.query_all(self.system_prompt, questions)
        return responses
    
    def _export_evaluation_report(self,
                                export_path: str,
                                filename: str,
                                columns: List[str],
                                data: List[Tuple[Any, ...]]) -> None:
        """Generic method to export evaluation reports
        
        Args:
            export_path: Directory path to save the report
            filename: Name of the file to save
            columns: Column headers for the report
            data: List of tuples containing the data rows
        """
        if export_path is not None:
            Export2CSV(
                columns=columns,
                data=data,
                export_path=os.path.join(export_path, filename)
            ).export2csv()
    
    def _prepare_evaluation_questions(self, 
                                    solution: SolutionResult, 
                                    user_prompt_template: str) -> Tuple[List, List, List, List]:
        """Prepare questions for evaluation from solution matrices
        
        Args:
            solution: SolutionResult containing questions and responses
            user_prompt_template: Template string with {question} and {response} placeholders
            
        Returns:
            format_questions: List of formatted questions
        """
        solution_matrices = solution._to_matrix()
        questions = [matrix[3] for matrix in solution_matrices]
        responses = [matrix[6] for matrix in solution_matrices]
        
        # Format questions for evaluation
        format_questions = [user_prompt_template.format(
            question=question,
            response=response
        ) for (question, response) in zip(questions, responses)]
        
        return format_questions
    
    def _prepare_evaluation_questions_with_products(self, 
                                    solution: SolutionResult, 
                                    user_prompt_template: str) -> Tuple[List, List, List, List]:
        """Prepare questions for evaluation from solution matrices
        
        Args:
            solution: SolutionResult containing questions and responses
            user_prompt_template: Template string with {question} and {response} placeholders
            
        Returns:
            format_questions: List of formatted questions
        """
        solution_matrices = solution._to_matrix()
        questions = [matrix[3] for matrix in solution_matrices]
        responses = [matrix[6] for matrix in solution_matrices]
        products = [matrix[7] for matrix in solution_matrices]
        
        # Format questions for evaluation
        format_questions = [user_prompt_template.format(
            question=question,
            response=response,
            products=products
        ) for (question, response, products) in zip(questions, responses, products)]
        
        return format_questions