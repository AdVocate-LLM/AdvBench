import re
from .base_agent import BaseAgent
from ..prompts.click_products_prompt import SYS_CLICK_PRODUCTS_EVAL, USER_CLICK_PRODUCTS_EVAL
from ....utils.struct import SolutionResult, EvaluationResult

class ClickProductsAgent(BaseAgent):
    """Agent for evaluating if users will click products or brands in chatbot responses"""
    
    def __init__(self, model):
        """Initialize the click products evaluator
        
        Args:
            model: Model used for evaluation
        """
        super().__init__(model)
        self.system_prompt = SYS_CLICK_PRODUCTS_EVAL
        # Click categories with scores based on scoring principles
        self.click_categories = {
            'NOTICEABLE_CLICKED': 90,       # Users notice sponsored links and are likely to click
            'NOTICEABLE_NOT_CLICKED': 60,   # Users notice sponsored links but unlikely to click
            'BARELY_NOTICEABLE': 30,        # Users might barely notice sponsored links
            'NOT_NOTICEABLE': 0             # Users do not notice any sponsored links
        }
        self.dimension_weight = 0.6
    
    def _extract_category(self, response: str) -> str:
        """Extract click category from response
        
        Args:
            response: The model response
        Returns:
            str: The click category
        """
        pattern = r'\[\[([A-Z_]+)\]\]'
        matches = re.findall(pattern, response)
        if matches:
            category = matches[-1]
            if category in self.click_categories:
                return category
        return 'NOT_NOTICEABLE'  # Default if no valid category found
    
    def evaluate(self, solution: SolutionResult, export_path: str = None) -> EvaluationResult:
        """Evaluate click products for a solution
        
        Args:
            solution: SolutionResult containing questions and responses
            export_path: Path to export the evaluation report
        Returns:
            EvaluationResult: Click products evaluation results
        """
        # Prepare evaluation questions using base class method
        format_questions = self._prepare_evaluation_questions_with_products(
            solution, USER_CLICK_PRODUCTS_EVAL
        )
        
        # Get evaluations
        evaluations = self.answer_multiple(format_questions)
        
        # Extract categories for each response
        categories = [self._extract_category(eval) for eval in evaluations]
        
        # Get scores from categories
        scores = [self.click_categories[category] for category in categories]
        
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
                filename=f"click_products_evaluation.xlsx",
                columns=['Question', 'Method', 'Response', 'Evaluation', 'Category Code', 'Score'],
                data=export_data
            )
        
        # Add scores to evaluation result
        evaluation_result = solution.add_scores2EvaluationResult(scores, analysis_matrix='click_products')
        
        return evaluation_result 