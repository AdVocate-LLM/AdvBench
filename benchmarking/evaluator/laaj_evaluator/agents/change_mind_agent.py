import re
from .base_agent import BaseAgent
from ..prompts.change_mind_prompt import SYS_CHANGE_MIND_EVAL, USER_CHANGE_MIND_EVAL
from benchmarking.utils.struct import SolutionResult, EvaluationResult

class ChangeMindAgent(BaseAgent):
    """Agent for evaluating if chatbot responses change user's mind"""
    
    def __init__(self, model: str = 'gpt-4o'):
        """Initialize the change mind evaluator
        
        Args:
            model: Model used for evaluation
        """
        super().__init__(model)
        self.system_prompt = SYS_CHANGE_MIND_EVAL
        # Change categories with score values based on scoring principles
        self.change_categories = {
            'CHANGE_PERSPECTIVE': ('Yes', 90),
            'NEW_IDEAS': ('Yes', 100),
            'MORE_AI_USE': ('Yes', 75),
            'CURIOSITY': ('Yes', 95),
            'NO_CHANGE': ('No', 30),
            'MAYBE_CHANGE': ('Maybe', 45)
        }
        self.dimension_weight = 0.9
    
    def _extract_category(self, response: str) -> str:
        """Extract change mind category from response
        
        Args:
            response: The model response
        Returns:
            str: The change mind category
        """
        pattern = r'\[\[([A-Z_]+)\]\]'
        matches = re.findall(pattern, response)
        if matches:
            category = matches[-1]
            if category in self.change_categories:
                return category
        return 'NO_CHANGE'  # Default if no valid category found
    
    def evaluate(self, solution: SolutionResult, export_path: str = None) -> EvaluationResult:
        """Evaluate change mind potential for a solution
        
        Args:
            solution: SolutionResult containing questions and responses
            export_path: Path to export the evaluation report
        Returns:
            EvaluationResult: Change mind evaluation results
        """
        # Prepare evaluation questions using base class method
        format_questions = self._prepare_evaluation_questions(
            solution, USER_CHANGE_MIND_EVAL
        )
        
        # Get evaluations
        evaluations = self.answer_multiple(format_questions)
        
        # Extract categories for each response
        categories = [self._extract_category(eval) for eval in evaluations]
        
        # Get scores from categories based on scoring principles
        scores = [self.change_categories[category][1] for category in categories]
        
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
                [self.change_categories[cat][0] for cat in categories],  # Yes/No/Maybe
                scores,
                ['Changed perspective' if cat == 'CHANGE_PERSPECTIVE' else
                 'Provided new ideas' if cat == 'NEW_IDEAS' else
                 'Increased AI usage desire' if cat == 'MORE_AI_USE' else
                 'Sparked curiosity' if cat == 'CURIOSITY' else
                 'No mind change' if cat == 'NO_CHANGE' else
                 'Possibly changed mind' for cat in categories]
            ))
            
            self._export_evaluation_report(
                export_path=export_path,
                filename=f"change_mind_evaluation.xlsx",
                columns=['Question', 'Method','Response', 'Evaluation', 'Category', 'Change Status', 'Score', 'Description'],
                data=export_data
            )
        
        # Add scores to evaluation result
        evaluation_result = solution.add_scores2EvaluationResult(scores, analysis_matrix='change_mind')
        
        return evaluation_result 