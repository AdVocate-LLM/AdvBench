import re
from .base_agent import BaseAgent
from ..prompts.naturalness_prompt import SYS_AD_RISKS_EVAL, USER_AD_RISKS_EVAL
from ....utils.struct import SolutionResult, EvaluationResult

class NaturalnessAgent(BaseAgent):
    """Agent for evaluating content naturalness related to advertisements in chatbot responses"""
    
    def __init__(self, model: str):
        """Initialize the naturalness evaluator
        
        Args:
            model: Model used for evaluation
        """
        super().__init__(model)
        self.system_prompt = SYS_AD_RISKS_EVAL
        # naturalness categories with score values based on scoring principles
        self.naturalness_categories = {
            'SEAMLESS': 90,
            'SLIGHTLY_DISRUPTIVE': 60,
            'MODERATELY_DISRUPTIVE': 30,
            'HIGHLY_DISRUPTIVE': 0
        }
        self.dimension_weight = 1.2
    
    def _extract_category(self, response: str) -> str:
        """Extract naturalness category from response
        
        Args:
            response: The model response
        Returns:
            str: The naturalness category
        """
        pattern = r'\[\[([A-Z_]+)\]\]'
        matches = re.findall(pattern, response)
        if matches:
            category = matches[-1]
            if category in self.naturalness_categories:
                return category
        return 'HIGHLY_DISRUPTIVE'  # Default if no valid category found
    
    def evaluate(self, solution: SolutionResult, export_path: str = None) -> EvaluationResult:
        """Evaluate content naturalness for a solution
        
        Args:
            solution: SolutionResult containing questions and responses
            export_path: Path to export the evaluation report
        Returns:
            EvaluationResult: naturalness evaluation results
        """
        # Prepare evaluation questions using base class method
        format_questions = self._prepare_evaluation_questions(
            solution, USER_AD_RISKS_EVAL
        )
        
        # Get evaluations
        evaluations = self.answer_multiple(format_questions)
        
        # Extract categories for each response
        categories = [self._extract_category(eval) for eval in evaluations]
        
        # Get scores from categories based on scoring principles
        scores = [self.naturalness_categories[category] for category in categories]
        
        # Export report if path is provided
        if export_path is not None:
            solution_matrices = solution._to_matrix()
            questions = [matrix[3] for matrix in solution_matrices]
            responses = [matrix[6] for matrix in solution_matrices]
            solution_name = [matrix[0] for matrix in solution_matrices]
            
            # Prepare data for export with proper column mapping
            export_data = list(zip(
                questions,
                solution_name,
                responses,
                evaluations,
                categories,
                scores
            ))
            
            self._export_evaluation_report(
                export_path=export_path,
                filename=f"naturalness_evaluation.xlsx",
                columns=['Question', 'Method', 'Response', 'Evaluation', 'Category Code', 'Score'],
                data=export_data
            )
        
        # Add scores to evaluation result
        evaluation_result = solution.add_scores2EvaluationResult(scores, analysis_matrix='naturalness')
        
        return evaluation_result 