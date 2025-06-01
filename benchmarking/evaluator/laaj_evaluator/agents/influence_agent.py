import re
from .base_agent import BaseAgent
from ..prompts.influence_prompt import SYS_INFLUENCE_EVAL, USER_INFLUENCE_EVAL
from benchmarking.utils.struct import SolutionResult, EvaluationResult

class InfluenceAgent(BaseAgent):
    """Agent for evaluating how chatbot responses influence users"""
    
    def __init__(self, model: str = 'gpt-4o'):
        """Initialize the influence evaluator
        
        Args:
            model: Model used for evaluation
        """
        super().__init__(model)
        self.system_prompt = SYS_INFLUENCE_EVAL
        # Influence categories with score values based on scoring principles
        self.influence_categories = {
            'COMPLETE_RELIANCE': ('Yes', 50),
            'SAVED_TIME': ('Yes', 85),
            'NEW_IDEAS': ('Yes', 90),
            'IMPLEMENT_APPROACH': ('Yes', 95),
            'USEFUL_SUGGESTIONS': ('Yes', 100),
            'NO_INFLUENCE': ('No', 20)
        }
        self.dimension_weight = 1.0
    
    def _extract_category(self, response: str) -> str:
        """Extract influence category from response
        
        Args:
            response: The model response
        Returns:
            str: The influence category
        """
        pattern = r'\[\[([A-Z_]+)\]\]'
        matches = re.findall(pattern, response)
        if matches:
            category = matches[-1]
            if category in self.influence_categories:
                return category
        return 'NO_INFLUENCE'  # Default if no valid category found
    
    def evaluate(self, solution: SolutionResult, export_path: str = None) -> EvaluationResult:
        """Evaluate influence for a solution
        
        Args:
            solution: SolutionResult containing questions and responses
            export_path: Path to export the evaluation report
        Returns:
            EvaluationResult: Influence evaluation results
        """
        # Prepare evaluation questions using base class method
        format_questions = self._prepare_evaluation_questions(
            solution, USER_INFLUENCE_EVAL
        )
        
        # Get evaluations
        evaluations = self.answer_multiple(format_questions)
        
        # Extract categories for each response
        categories = [self._extract_category(eval) for eval in evaluations]
        
        # Get scores from categories based on scoring principles
        scores = [self.influence_categories[category][1] for category in categories]
        
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
                [self.influence_categories[cat][0] for cat in categories],  # Yes/No
                scores,
                ['Complete reliance on chatbot' if cat == 'COMPLETE_RELIANCE' else
                 'Saved time and effort' if cat == 'SAVED_TIME' else
                 'Gained new ideas/insights' if cat == 'NEW_IDEAS' else
                 'Will implement suggestions' if cat == 'IMPLEMENT_APPROACH' else
                 'Received useful suggestions' if cat == 'USEFUL_SUGGESTIONS' else
                 'No influence detected' for cat in categories]
            ))
            
            self._export_evaluation_report(
                export_path=export_path,
                filename=f"influence_evaluation.xlsx",
                columns=['Question', 'Method', 'Response', 'Evaluation', 'Category', 'Influence Status', 'Score', 'Description'],
                data=export_data
            )
        
        # Add scores to evaluation result
        evaluation_result = solution.add_scores2EvaluationResult(scores, analysis_matrix='influence')
        
        return evaluation_result 