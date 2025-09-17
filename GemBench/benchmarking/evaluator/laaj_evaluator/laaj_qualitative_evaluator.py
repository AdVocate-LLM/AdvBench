from ..base_evaluator import BaseEvaluator
from .agents.trust_agent import TrustAgent
from .agents.accuracy_agent import AccuracyAgent
from .agents.personality_agent import PersonalityAgent
from .agents.notice_products_agent import NoticeProductsAgent
from .agents.naturalness_agent import NaturalnessAgent
from .agents.click_products_agent import ClickProductsAgent
from ...utils.struct import SolutionResult, EvaluationResult
from typing import List, Any


class LAJQualitativeEvaluator(BaseEvaluator):
    """Qualitative Evaluator for comprehensive chatbot evaluation
    
    This evaluator implements the Qualitative Evaluation Ontology:
    1. User Satisfaction
       - Accuracy (Response relevance and accuracy to users - whether responses directly answer questions)
       - naturalness (Content naturalness related to advertisements)
       - Personality (Personality traits exhibited by the chatbot)
       - Trust (Whether users trust the chatbot's responses)
    2. User Engagement
       - Ad Notice (Whether users will notice products or brands)
       - Ad Click (Whether users will click products or brands)
    """
    
    ANALYSIS_MATRIXES = [
        "accuracy_evaluation",
        "naturalness_evaluation",
        "personality_evaluation",
        "trust_evaluation",
        "notice_products_evaluation",
        "click_products_evaluation",
    ]
    
    def __init__(self, 
                output_dir: str,
                judge_model: str,
                results: SolutionResult):
        """Initialize the qualitative evaluator with all evaluation agents
        
        Args:
            output_dir: Directory to save results
            results: SolutionResult to evaluate
            judge_model: Model to use for evaluation
        """
        super().__init__(output_dir=output_dir, results=results)
        
        # Initialize all evaluation agents
        self.trust_agent = TrustAgent(judge_model)
        self.accuracy_agent = AccuracyAgent(judge_model)
        self.personality_agent = PersonalityAgent(judge_model)
        self.notice_products_agent = NoticeProductsAgent(judge_model)
        self.naturalness_agent = NaturalnessAgent(judge_model)
        self.click_products_agent = ClickProductsAgent(judge_model)
        
    def get_analysis_matrixes(self) -> List[str]:
        return self.ANALYSIS_MATRIXES
    
    def get_matrices(self, matrix_name: str, records: Any, is_saved: bool = True) -> EvaluationResult:
        """Get the analysis matrix results for a specific evaluation dimension
        
        Args:
            matrix_name: Name of the analysis matrix
            records: The SolutionResult to evaluate
            is_saved: Whether to save results
            
        Returns:
            EvaluationResult: Results of the evaluation
        """
        if not isinstance(records, SolutionResult):
            raise ValueError(f"Invalid records type: {type(records)}, expected SolutionResult")
        
        # Map matrix names to corresponding evaluation methods
        # Qualitative Evaluation Ontology
        # ├── 1. User Satisfaction
        # │   ├── 1.1 Accuracy
        # │   │   └── Response relevance and accuracy to users (whether responses directly answer questions)
        # │   ├── 1.2 Naturalness
        # │   │   └── Content naturalness related to advertisements
        # │   ├── 1.3 Personality
        # │   │   └── Personality traits exhibited by the chatbot
        # │   └── 1.4 Trust
        # │       └── Whether users trust the chatbot's responses
        # └── 2. User Engagement
        #     ├── 2.1 Ad Notice
        #     │   └── Whether users will notice products or brands
        #     └── 2.2 Ad Click
        #         └── Whether users will click products or brands
        evaluation_methods = {
            "trust_evaluation": lambda sol: self.trust_agent.evaluate(sol, self.output_dir if is_saved else None),
            "accuracy_evaluation": lambda sol: self.accuracy_agent.evaluate(sol, self.output_dir if is_saved else None),
            "personality_evaluation": lambda sol: self.personality_agent.evaluate(sol, self.output_dir if is_saved else None),
            "notice_products_evaluation": lambda sol: self.notice_products_agent.evaluate(sol, self.output_dir if is_saved else None),
            "naturalness_evaluation": lambda sol: self.naturalness_agent.evaluate(sol, self.output_dir if is_saved else None),
            "click_products_evaluation": lambda sol: self.click_products_agent.evaluate(sol, self.output_dir if is_saved else None),
        }
        
        if matrix_name in evaluation_methods:
            return evaluation_methods[matrix_name](records)
        else:
            raise ValueError(f"Invalid matrix name: {matrix_name}")
    
    def evaluate(self, analysis_matrixes: List[str] = None, is_saved: bool = True) -> EvaluationResult:
        """Evaluate the solution across all qualitative dimensions
        
        Args:
            analysis_matrixes: List of specific matrices to evaluate (default: all)
            is_saved: Whether to save results
            
        Returns:
            EvaluationResult: Combined results from all evaluations
        """
        evaluation_result = EvaluationResult()
        
        if analysis_matrixes is None:
            analysis_matrixes = self.ANALYSIS_MATRIXES
        
        # Run each evaluation matrix on all solutions
        for matrix_name in analysis_matrixes:
            if matrix_name in self.ANALYSIS_MATRIXES:
                self.section(f"Running {matrix_name}")
                try:
                    matrix_result = self.get_matrices(
                        matrix_name=matrix_name,
                        records=self.results,  # Pass all results, not grouped by solution
                        is_saved=is_saved
                    )
                    evaluation_result += matrix_result
                except Exception as e:
                    self.error(f"Error in {matrix_name}: {str(e)}")
        
        return evaluation_result 