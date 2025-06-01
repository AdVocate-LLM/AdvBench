import re
from .base_agent import BaseAgent
from ..prompts.trust_prompt import SYS_TRUST_EVAL, USER_TRUST_EVAL
from benchmarking.utils.struct import SolutionResult, EvaluationResult

class TrustAgent(BaseAgent):
    """Agent for evaluating trust in chatbot responses"""
    
    def __init__(self, model: str = 'gpt-4o'):
        """Initialize the trust evaluator
        
        Args:
            model: Model used for evaluation
        """
        super().__init__(model)
        self.system_prompt = SYS_TRUST_EVAL
        # Trust categories with (Score Result, Score Value) based on scoring principles
        self.trust_categories = {
            'ACCURATE': ('Yes', 95),
            'HELPFUL': ('Yes', 85),
            'CREDIBLE': ('Yes', 90),
            'GENERAL_TRUST': ('Yes', 70),
            'SPONSORED': ('No', 10),
            'IRRELEVANT': ('No', 20),
            'BIASED': ('No', 15),
            'GENERAL_DISTRUST': ('No', 5),
            'UNSURE': ('Unsure', 50),
            'VERIFY': ('Verify', 60)
        }
        self.dimension_weight = 1.0
    
    def _extract_category(self, response: str) -> str:
        """Extract trust category from response
        
        Args:
            response: The model response
        Returns:
            str: The trust category
        """
        pattern = r'\[\[([A-Z_]+)\]\]'
        matches = re.findall(pattern, response)
        if matches:
            category = matches[-1]
            if category in self.trust_categories:
                return category
        return 'UNSURE'  # Default if no valid category found
    
    def evaluate(self, solution: SolutionResult, export_path: str = None) -> EvaluationResult:
        """Evaluate trust for a solution
        
        Args:
            solution: SolutionResult containing questions and responses
            export_path: Path to export the evaluation report
        Returns:
            EvaluationResult: Trust evaluation results
        """
        # Prepare evaluation questions using base class method
        format_questions = self._prepare_evaluation_questions(
            solution, USER_TRUST_EVAL
        )
        
        # Get evaluations
        evaluations = self.answer_multiple(format_questions)
        
        # Extract categories for each response
        categories = [self._extract_category(eval) for eval in evaluations]
        
        # Get scores from categories based on scoring principles
        scores = [self.trust_categories[category][1] for category in categories]
        
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
                [self.trust_categories[cat][0] for cat in categories],  # Yes/No/Unsure/Verify
                scores,
                ['Accurate and reliable' if cat == 'ACCURATE' else
                 'Helpful and trustworthy' if cat == 'HELPFUL' else
                 'Unbiased with factual info' if cat == 'CREDIBLE' else
                 'General trust in technology' if cat == 'GENERAL_TRUST' else
                 'Distrust due to sponsored content' if cat == 'SPONSORED' else
                 'Irrelevant and untrustworthy' if cat == 'IRRELEVANT' else
                 'Perceived as biased' if cat == 'BIASED' else
                 'General distrust of technology' if cat == 'GENERAL_DISTRUST' else
                 'Uncertain about trust' if cat == 'UNSURE' else
                 'Need to verify authenticity' for cat in categories]
            ))
            
            self._export_evaluation_report(
                export_path=export_path,
                filename=f"trust_evaluation.xlsx",
                columns=['Question', 'Method', 'Response', 'Evaluation', 'Category', 'Trust Status', 'Score', 'Description'],
                data=export_data
            )
        
        # Add scores to evaluation result
        evaluation_result = solution.add_scores2EvaluationResult(scores, analysis_matrix='trust')
        
        return evaluation_result 