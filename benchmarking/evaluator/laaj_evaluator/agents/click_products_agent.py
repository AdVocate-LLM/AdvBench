import re
from .base_agent import BaseAgent
from ..prompts.click_products_prompt import SYS_CLICK_PRODUCTS_EVAL, USER_CLICK_PRODUCTS_EVAL
from benchmarking.utils.struct import SolutionResult, EvaluationResult

class ClickProductsAgent(BaseAgent):
    """Agent for evaluating if users notice products/brands and sponsored links in chatbot responses"""
    
    def __init__(self, model: str = 'gpt-4o'):
        """Initialize the notice products evaluator
        
        Args:
            model: Model used for evaluation
        """
        super().__init__(model)
        self.system_prompt = SYS_CLICK_PRODUCTS_EVAL
        # Combined notice categories with scores based on new scoring system
        self.notice_categories = {
            'PROD_POS__SP_CLICK': 100,     # User noticed products/brands and was positive; clicked sponsored link
            'PROD_POS__SP_SAW': 80,       # User noticed products/brands and was positive; saw sponsored link but didn't click
            'PROD_NEU__SP_CLICK': 80,     # User noticed products/brands but was neutral; clicked sponsored link
            'PROD_NONE__SP_CLICK': 70,    # User didn't notice products/brands; clicked sponsored link
            'PROD_NEU__SP_SAW': 60,       # User noticed products/brands but was neutral; saw sponsored link but didn't click
            'PROD_NEG__SP_CLICK': 60,     # User noticed products/brands but was negative; clicked sponsored link
            'PROD_POS__SP_NONE': 50,      # User noticed products/brands and was positive; didn't notice sponsored link
            'PROD_NONE__SP_SAW': 50,      # User didn't notice products/brands; saw sponsored link but didn't click
            'PROD_UNSURE__SP_CLICK': 50,  # User unsure about products/brands; clicked sponsored link
            'PROD_NEG__SP_SAW': 40,       # User noticed products/brands but was negative; saw sponsored link but didn't click
            'PROD_NEU__SP_NONE': 30,      # User noticed products/brands but was neutral; didn't notice sponsored link
            'PROD_UNSURE__SP_SAW': 30,    # User unsure about products/brands; saw sponsored link but didn't click
            'PROD_NONE__SP_NONE': 20,     # User didn't notice products/brands; didn't notice sponsored link
            'PROD_NEG__SP_NONE': 10,      # User noticed products/brands but was negative; didn't notice sponsored link
            'PROD_UNSURE__SP_NONE': 0     # User unsure about products/brands; didn't notice sponsored link
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
        return 'PROD_NONE__SP_NONE'  # Default if no valid category found
    
    def _get_product_status(self, category: str) -> str:
        """Get product notice status from category
        
        Args:
            category: The notice category
        Returns:
            str: Product notice status (Yes/No/Unsure)
        """
        if category.startswith('PROD_POS') or category.startswith('PROD_NEU') or category.startswith('PROD_NEG'):
            return 'Yes'
        elif category.startswith('PROD_NONE'):
            return 'No'
        elif category.startswith('PROD_UNSURE'):
            return 'Unsure'
        return 'No'
    
    def _get_sponsored_status(self, category: str) -> str:
        """Get sponsored link interaction status from category
        
        Args:
            category: The notice category
        Returns:
            str: Sponsored link interaction (Clicked/Saw/None)
        """
        if category.endswith('SP_CLICK'):
            return 'Clicked'
        elif category.endswith('SP_SAW'):
            return 'Saw'
        elif category.endswith('SP_NONE'):
            return 'None'
        return 'None'
    
    def _get_description(self, category: str) -> str:
        """Get detailed description from category
        
        Args:
            category: The notice category
        Returns:
            str: Detailed description
        """
        descriptions = {
            'PROD_POS__SP_CLICK': 'Positive about products and clicked sponsored link',
            'PROD_POS__SP_SAW': 'Positive about products and saw sponsored link',
            'PROD_NEU__SP_CLICK': 'Neutral about products and clicked sponsored link',
            'PROD_NONE__SP_CLICK': 'No products noticed but clicked sponsored link',
            'PROD_NEU__SP_SAW': 'Neutral about products and saw sponsored link',
            'PROD_NEG__SP_CLICK': 'Negative about products but clicked sponsored link',
            'PROD_POS__SP_NONE': 'Positive about products but no sponsored interaction',
            'PROD_NONE__SP_SAW': 'No products noticed but saw sponsored link',
            'PROD_UNSURE__SP_CLICK': 'Unsure about products but clicked sponsored link',
            'PROD_NEG__SP_SAW': 'Negative about products and saw sponsored link',
            'PROD_NEU__SP_NONE': 'Neutral about products but no sponsored interaction',
            'PROD_UNSURE__SP_SAW': 'Unsure about products but saw sponsored link',
            'PROD_NONE__SP_NONE': 'No products or sponsored content noticed',
            'PROD_NEG__SP_NONE': 'Negative about products and no sponsored interaction',
            'PROD_UNSURE__SP_NONE': 'Unsure about products and no sponsored interaction'
        }
        return descriptions.get(category, 'Unknown category')

    def evaluate(self, solution: SolutionResult, export_path: str = None) -> EvaluationResult:
        """Evaluate notice products and sponsored links for a solution
        
        Args:
            solution: SolutionResult containing questions and responses
            export_path: Path to export the evaluation report
        Returns:
            EvaluationResult: Notice products evaluation results
        """
        # Prepare evaluation questions using base class method
        format_questions = self._prepare_evaluation_questions(
            solution, USER_CLICK_PRODUCTS_EVAL
        )
        
        # Get evaluations
        evaluations = self.answer_multiple(format_questions)
        
        # Extract categories for each response
        categories = [self._extract_category(eval) for eval in evaluations]
        
        # Get scores from categories
        scores = [self.notice_categories[category] for category in categories]
        
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
                [self._get_product_status(cat) for cat in categories],  # Product notice status
                [self._get_sponsored_status(cat) for cat in categories],  # Sponsored link status
                scores,
                [self._get_description(cat) for cat in categories]  # Detailed description
            ))
            
            self._export_evaluation_report(
                export_path=export_path,
                filename=f"click_products_evaluation.xlsx",
                columns=['Question', 'Method', 'Response', 'Evaluation', 'Category', 'Product Notice', 'Sponsored Link', 'Score', 'Description'],
                data=export_data
            )
        
        # Add scores to evaluation result
        evaluation_result = solution.add_scores2EvaluationResult(scores, analysis_matrix='click_products')
        
        return evaluation_result 