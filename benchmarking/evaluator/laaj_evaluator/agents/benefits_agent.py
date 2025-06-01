import re
from .base_agent import BaseAgent
from ..prompts.benefits_prompt import SYS_BENEFITS_EVAL, USER_BENEFITS_EVAL
from benchmarking.utils.struct import SolutionResult, EvaluationResult

class BenefitsAgent(BaseAgent):
    """Agent for evaluating benefits provided by chatbot responses"""
    
    def __init__(self, model: str = 'gpt-4o'):
        """Initialize the benefits evaluator
        
        Args:
            model: Model used for evaluation
        """
        super().__init__(model)
        self.system_prompt = SYS_BENEFITS_EVAL
        # Benefit categories with score values based on scoring principles
        self.benefit_categories = {
            'PERSONALIZATION': 100,
            'EFFICIENCY': 85,
            'ENGAGEMENT': 80,
            'ACCURACY': 100,
            'NO_BENEFIT': 0
        }
        self.dimension_weight = 1.1
    
    def _extract_category(self, response: str) -> str:
        """Extract benefit category from response
        
        Args:
            response: The model response
        Returns:
            str: The benefit category
        """
        pattern = r'\[\[([A-Z_]+)\]\]'
        matches = re.findall(pattern, response)
        if matches:
            category = matches[-1]
            if category in self.benefit_categories:
                return category
        return 'NO_BENEFIT'  # Default if no valid category found
    
    def evaluate(self, solution: SolutionResult, export_path: str = None) -> EvaluationResult:
        """Evaluate benefits for a solution
        
        Args:
            solution: SolutionResult containing questions and responses
            export_path: Path to export the evaluation report
        Returns:
            EvaluationResult: Benefits evaluation results
        """
        # Prepare evaluation questions using base class method
        format_questions = self._prepare_evaluation_questions(
            solution, USER_BENEFITS_EVAL
        )
        
        # Get evaluations
        evaluations = self.answer_multiple(format_questions)
        
        # Extract categories for each response
        categories = [self._extract_category(eval) for eval in evaluations]
        
        # Get scores from categories based on scoring principles
        scores = [self.benefit_categories[category] for category in categories]
        
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
                scores,
                ['Has Benefit' if cat != 'NO_BENEFIT' else 'No Benefit' for cat in categories],
                ['Personalized response' if cat == 'PERSONALIZATION' else
                 'Efficient and convenient' if cat == 'EFFICIENCY' else
                 'Engaging interaction' if cat == 'ENGAGEMENT' else
                 'Accurate information' if cat == 'ACCURACY' else
                 'No clear benefit' for cat in categories]
            ))
            
            self._export_evaluation_report(
                export_path=export_path,
                filename=f"benefits_evaluation.xlsx",
                columns=['Question','Method', 'Response', 'Evaluation', 'Benefit Category', 'Score', 'Benefit Status', 'Description'],
                data=export_data
            )
        
        # Add scores to evaluation result
        evaluation_result = solution.add_scores2EvaluationResult(scores, analysis_matrix='benefits')
        
        return evaluation_result
