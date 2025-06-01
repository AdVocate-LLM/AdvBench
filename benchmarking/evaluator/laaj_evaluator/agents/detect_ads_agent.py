import re
from .base_agent import BaseAgent
from ..prompts.detect_ads_prompt import SYS_DETECT_ADS_EVAL, USER_DETECT_ADS_EVAL
from benchmarking.utils.struct import SolutionResult, EvaluationResult

class DetectAdsAgent(BaseAgent):
    """Agent for evaluating users' ability to detect ads in chatbot responses"""
    
    def __init__(self, model: str = 'gpt-4o'):
        """Initialize the detect ads evaluator
        
        Args:
            model: Model used for evaluation
        """
        super().__init__(model)
        self.system_prompt = SYS_DETECT_ADS_EVAL
        # Detect categories with (Score Result, Score Value) based on scoring principles
        self.detect_categories = {
            'PRODUCT_BRAND': ('Yes', 100),
            'IRRELEVANT_CONTEXT': ('Yes', 85),
            'VISUAL_CUES': ('Yes', 95),
            'OTHER_DETECTABLE': ('Yes', 80),
            'NOT_DETECTABLE': ('No', 0),
            'UNSURE': ('Unsure', 30)
        }
        self.dimension_weight = 0.8
    
    def _extract_category(self, response: str) -> str:
        """Extract detect category from response
        
        Args:
            response: The model response
        Returns:
            str: The detect category
        """
        pattern = r'\[\[([A-Z_]+)\]\]'
        matches = re.findall(pattern, response)
        if matches:
            category = matches[-1]
            if category in self.detect_categories:
                return category
        return 'UNSURE'  # Default if no valid category found
    
    def evaluate(self, solution: SolutionResult, export_path: str = None) -> EvaluationResult:
        """Evaluate ad detectability for a solution
        
        Args:
            solution: SolutionResult containing questions and responses
            export_path: Path to export the evaluation report
        Returns:
            EvaluationResult: Detect ads evaluation results
        """
        # Prepare evaluation questions using base class method
        format_questions = self._prepare_evaluation_questions(
            solution, USER_DETECT_ADS_EVAL
        )
        
        # Get evaluations
        evaluations = self.answer_multiple(format_questions)
        
        # Extract categories for each response
        categories = [self._extract_category(eval) for eval in evaluations]
        
        # Get scores from categories based on scoring principles
        scores = [self.detect_categories[category][1] for category in categories]
        
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
                [self.detect_categories[cat][0] for cat in categories],  # Yes/No/Unsure
                scores,
                ['Direct product/brand mention' if cat == 'PRODUCT_BRAND' else
                 'Irrelevant content deviation' if cat == 'IRRELEVANT_CONTEXT' else
                 'Visual ad elements present' if cat == 'VISUAL_CUES' else
                 'Other detectable factors' if cat == 'OTHER_DETECTABLE' else
                 'No ads detected' if cat == 'NOT_DETECTABLE' else
                 'Uncertain detection' for cat in categories]
            ))
            
            self._export_evaluation_report(
                export_path=export_path,
                filename=f"detect_ads_evaluation.xlsx",
                columns=['Question', 'Method', 'Response', 'Evaluation', 'Category', 'Detection Status', 'Score', 'Description'],
                data=export_data
            )
        
        # Add scores to evaluation result
        evaluation_result = solution.add_scores2EvaluationResult(scores, analysis_matrix='detect_ads')
        
        return evaluation_result 