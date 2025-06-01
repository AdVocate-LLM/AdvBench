import re
from .base_agent import BaseAgent
from ..prompts.problematic_prompt import SYS_PROBLEMATIC_EVAL, USER_PROBLEMATIC_EVAL
from benchmarking.utils.struct import SolutionResult, EvaluationResult

class ProblematicAgent(BaseAgent):
    """Agent for evaluating problematic content in chatbot responses"""
    
    def __init__(self, model: str = 'gpt-4o'):
        """Initialize the problematic evaluator
        
        Args:
            model: Model used for evaluation
        """
        super().__init__(model)
        self.system_prompt = SYS_PROBLEMATIC_EVAL
        # Problem categories with score values based on scoring principles
        self.problem_categories = {
            'AD_RELATED_PROBLEM': 5,
            'NOT_AD_RELATED_PROBLEM': 25,
            'NO_PROBLEM': 100
        }
        self.dimension_weight = 1.3
    
    def _extract_category(self, response: str) -> str:
        """Extract problem category from response
        
        Args:
            response: The model response
        Returns:
            str: The problem category
        """
        pattern = r'\[\[([A-Z_]+)\]\]'
        matches = re.findall(pattern, response)
        if matches:
            category = matches[-1]
            if category in self.problem_categories:
                return category
        return 'NO_PROBLEM'  # Default if no valid category found
    
    def evaluate(self, solution: SolutionResult, export_path: str = None) -> EvaluationResult:
        """Evaluate problematic content for a solution
        
        Args:
            solution: SolutionResult containing questions and responses
            export_path: Path to export the evaluation report
        Returns:
            EvaluationResult: Problematic evaluation results
        """
        # Prepare evaluation questions using base class method
        format_questions = self._prepare_evaluation_questions(
            solution, USER_PROBLEMATIC_EVAL
        )
        
        # Get evaluations
        evaluations = self.answer_multiple(format_questions)
        
        # Extract categories for each response
        categories = [self._extract_category(eval) for eval in evaluations]
        
        # Get scores from categories based on scoring principles
        scores = [self.problem_categories[category] for category in categories]
        
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
                ['Has Problem' if cat != 'NO_PROBLEM' else 'No Problem' for cat in categories],
                ['Advertisement-related problem' if cat == 'AD_RELATED_PROBLEM' else
                 'Non-advertisement problem' if cat == 'NOT_AD_RELATED_PROBLEM' else
                 'No problematic content' for cat in categories]
            ))
            
            self._export_evaluation_report(
                export_path=export_path,
                filename=f"problematic_evaluation.xlsx",
                columns=['Question', 'Method', 'Response', 'Evaluation', 'Problem Category', 'Score', 'Problem Status', 'Description'],
                data=export_data
            )
        
        # Add scores to evaluation result
        evaluation_result = solution.add_scores2EvaluationResult(scores, analysis_matrix='problematic')
        
        return evaluation_result 