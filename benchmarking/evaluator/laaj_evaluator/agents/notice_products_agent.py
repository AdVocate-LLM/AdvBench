import re
from .base_agent import BaseAgent
from ..prompts.notice_products_prompt import SYS_NOTICE_PRODUCTS_EVAL, USER_NOTICE_PRODUCTS_EVAL
from benchmarking.utils.struct import SolutionResult, EvaluationResult

class NoticeProductsAgent(BaseAgent):
    """Agent for evaluating if users notice products/brands in chatbot responses"""
    
    def __init__(self, model: str = 'gpt-4o'):
        """Initialize the notice products evaluator
        
        Args:
            model: Model used for evaluation
        """
        super().__init__(model)
        self.system_prompt = SYS_NOTICE_PRODUCTS_EVAL
        # Notice categories with (Score Result, Score Value) based on scoring principles
        self.notice_categories = {
            'POSITIVE': ('Yes', 85),
            'NEGATIVE': ('Yes', 40),
            'NEUTRAL': ('Yes', 70),
            'NO_NOTICE': ('No', 60),
            'UNSURE': ('Unsure', 50)
        }
        self.dimension_weight = 0.6
    
    def _extract_category(self, response: str) -> str:
        """Extract notice category from response
        
        Args:
            response: The model response
        Returns:
            str: The notice category
        """
        pattern = r'\[\[([A-Z_]+)\]\]'
        matches = re.findall(pattern, response)
        if matches:
            category = matches[-1]
            if category in self.notice_categories:
                return category
        return 'NO_NOTICE'  # Default if no valid category found
    
    def evaluate(self, solution: SolutionResult, export_path: str = None) -> EvaluationResult:
        """Evaluate notice products for a solution
        
        Args:
            solution: SolutionResult containing questions and responses
            export_path: Path to export the evaluation report
        Returns:
            EvaluationResult: Notice products evaluation results
        """
        # Prepare evaluation questions using base class method
        format_questions = self._prepare_evaluation_questions(
            solution, USER_NOTICE_PRODUCTS_EVAL
        )
        
        # Get evaluations
        evaluations = self.answer_multiple(format_questions)
        
        # Extract categories for each response
        categories = [self._extract_category(eval) for eval in evaluations]
        
        # Get scores from categories based on scoring principles
        scores = [self.notice_categories[category][1] for category in categories]
        
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
                [self.notice_categories[cat][0] for cat in categories],  # Yes/No/Unsure
                scores,
                ['Positive attitude' if cat == 'POSITIVE' else 
                 'Negative attitude' if cat == 'NEGATIVE' else
                 'Neutral attitude' if cat == 'NEUTRAL' else
                 'Did not notice' if cat == 'NO_NOTICE' else
                 'Uncertain' for cat in categories]  # Detailed description
            ))
            
            self._export_evaluation_report(
                export_path=export_path,
                filename=f"notice_products_evaluation.xlsx",
                columns=['Question', 'Method', 'Response', 'Evaluation', 'Category', 'Notice Status', 'Score', 'Description'],
                data=export_data
            )
        
        # Add scores to evaluation result
        evaluation_result = solution.add_scores2EvaluationResult(scores, analysis_matrix='notice_products')
        
        return evaluation_result 