from benchmarking.evaluator.base_evaluator import BaseEvaluator
from benchmarking.evaluator.laaj_evaluator.agents.trust_agent import TrustAgent
from benchmarking.evaluator.laaj_evaluator.agents.benefits_agent import BenefitsAgent
from benchmarking.evaluator.laaj_evaluator.agents.personality_agent import PersonalityAgent
from benchmarking.evaluator.laaj_evaluator.agents.influence_agent import InfluenceAgent
from benchmarking.evaluator.laaj_evaluator.agents.change_mind_agent import ChangeMindAgent
from benchmarking.evaluator.laaj_evaluator.agents.notice_products_agent import NoticeProductsAgent
from benchmarking.evaluator.laaj_evaluator.agents.detect_ads_agent import DetectAdsAgent
from benchmarking.evaluator.laaj_evaluator.agents.ad_risks_agent import AdRisksAgent
from benchmarking.evaluator.laaj_evaluator.agents.problematic_agent import ProblematicAgent
from benchmarking.utils.struct import SolutionResult, EvaluationResult
from typing import List, Any


class LAJQualitativeEvaluator(BaseEvaluator):
    """Qualitative Evaluator for comprehensive chatbot evaluation
    
    This evaluator implements the Qualitative Evaluation Ontology:
    1. User Satisfaction
       - Credibility (Trust Chatbot)
       - Helpfulness (Benefits for Users)
       - Neutrality and Tone (Chatbot Personality)
    2. User Engagement
       - Convincingness (Influence Users, Change User's Mind)
       - Engagement with Ads (Notice Products/Brands, Detect Ads)
    3. Risk Assessment
       - Ad-Related Risks (Chatbot Advertising Risks, Any Problematic Responses)
    """
    
    ANALYSIS_MATRIXES = [
        "trust_evaluation",
        "benefits_evaluation",
        "personality_evaluation",
        "influence_evaluation",
        "change_mind_evaluation",
        "notice_products_evaluation",
        "detect_ads_evaluation",
        "ad_risks_evaluation",
        "problematic_evaluation"
    ]
    
    def __init__(self, 
                output_dir: str,
                results: SolutionResult,
                judge_model: str = 'gpt-4o'):
        """Initialize the qualitative evaluator with all evaluation agents
        
        Args:
            output_dir: Directory to save results
            results: SolutionResult to evaluate
            judge_model: Model to use for evaluation
        """
        super().__init__(output_dir=output_dir, results=results)
        
        # Initialize all evaluation agents
        self.trust_agent = TrustAgent(judge_model)
        self.benefits_agent = BenefitsAgent(judge_model)
        self.personality_agent = PersonalityAgent(judge_model)
        self.influence_agent = InfluenceAgent(judge_model)
        self.change_mind_agent = ChangeMindAgent(judge_model)
        self.notice_products_agent = NoticeProductsAgent(judge_model)
        self.detect_ads_agent = DetectAdsAgent(judge_model)
        self.ad_risks_agent = AdRisksAgent(judge_model)
        self.problematic_agent = ProblematicAgent(judge_model)
        
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
        # │   ├── 1.1 Credibility
        # │   │   └── Trust Chatbot
        # │   ├── 1.2 Helpfulness
        # │   │   └── Benefits for Users
        # │   └── 1.3 Neutrality and Tone
        # │       └── Chatbot Personality
        # ├── 2. User Engagement
        # │   ├── 2.1 Convincingness
        # │   │   ├── Influence Users
        # │   │   └── Change User's Mind
        # │   └── 2.2 Engagement with Ads
        # │       ├── Notice Products/Brands
        # │       ├── Notice/Click Sponsored Link
        # │       └── Able to Detect Chatbot Ads
        # └── 3. Risk Assessment
        #     └── 3.1 Ad-Related Risks
        #         ├── Chatbot Advertising Risks
        #         └── Any Problematic Responses
        evaluation_methods = {
            "trust_evaluation": lambda sol: self.trust_agent.evaluate(sol, self.output_dir if is_saved else None),
            "benefits_evaluation": lambda sol: self.benefits_agent.evaluate(sol, self.output_dir if is_saved else None),
            "personality_evaluation": lambda sol: self.personality_agent.evaluate(sol, self.output_dir if is_saved else None),
            "influence_evaluation": lambda sol: self.influence_agent.evaluate(sol, self.output_dir if is_saved else None),
            "change_mind_evaluation": lambda sol: self.change_mind_agent.evaluate(sol, self.output_dir if is_saved else None),
            "notice_products_evaluation": lambda sol: self.notice_products_agent.evaluate(sol, self.output_dir if is_saved else None),
            "detect_ads_evaluation": lambda sol: self.detect_ads_agent.evaluate(sol, self.output_dir if is_saved else None),
            "ad_risks_evaluation": lambda sol: self.ad_risks_agent.evaluate(sol, self.output_dir if is_saved else None),
            "problematic_evaluation": lambda sol: self.problematic_agent.evaluate(sol, self.output_dir if is_saved else None)
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