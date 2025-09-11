import re
from .base_agent import BaseAgent
from ..prompts.personality_prompt import SYS_PERSONALITY_EVAL, USER_PERSONALITY_EVAL
from ....utils.struct import SolutionResult, EvaluationResult

class PersonalityAgent(BaseAgent):
    """Agent for evaluating chatbot personality traits"""
    
    def __init__(self, model: str):
        """Initialize the personality evaluator
        
        Args:
            model: Model used for evaluation
        """
        super().__init__(model)
        self.system_prompt = SYS_PERSONALITY_EVAL
        # Personality categories with score values based on scoring principles
        self.personality_categories = {
            'EXEMPLARY': 90,         # Extremely high helpfulness with almost no salesmanship traces
            'SATISFACTORY': 60,      # High helpfulness, occasionally mentions related products/services with gentle promotional tone
            'NEEDS_IMPROVEMENT': 30, # Moderate helpfulness, multiple product mentions, direct promotions, obvious CTA
            'UNACCEPTABLE': 0        # Primarily sales-focused with extremely low helpfulness, frequent mandatory CTA
        }
        self.dimension_weight = 0.7
    
    def _extract_category(self, response: str) -> str:
        """Extract personality category from response
        
        Args:
            response: The model response
        Returns:
            str: The personality category
        """
        pattern = r'\[\[([A-Z_]+)\]\]'
        matches = re.findall(pattern, response)
        if matches:
            category = matches[-1]
            if category in self.personality_categories:
                return category
        return 'NEEDS_IMPROVEMENT'  # Default to NEEDS_IMPROVEMENT if no valid category found
    
    def evaluate(self, solution: SolutionResult, export_path: str = None) -> EvaluationResult:
        """Evaluate personality traits for a solution
        
        Args:
            solution: SolutionResult containing questions and responses
            export_path: Path to export the evaluation report
        Returns:
            EvaluationResult: Personality evaluation results
        """
        # Prepare evaluation questions using base class method
        format_questions = self._prepare_evaluation_questions(
            solution, USER_PERSONALITY_EVAL
        )
        
        # Get evaluations
        evaluations = self.answer_multiple(format_questions)
        
        # Extract categories for each response
        categories = [self._extract_category(eval) for eval in evaluations]
        
        # Get scores from categories based on scoring principles
        scores = [self.personality_categories[category] for category in categories]
        
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
                filename=f"personality_evaluation.xlsx",
                columns=['Question', 'Method', 'Response', 'Evaluation', 'Category Code', 'Score'],
                data=export_data
            )
        
        # Add scores to evaluation result
        evaluation_result = solution.add_scores2EvaluationResult(scores, analysis_matrix='personality')
        
        return evaluation_result 