import re
from .base_agent import BaseAgent
from ..prompts.personality_prompt import SYS_PERSONALITY_EVAL, USER_PERSONALITY_EVAL
from benchmarking.utils.struct import SolutionResult, EvaluationResult

class PersonalityAgent(BaseAgent):
    """Agent for evaluating chatbot personality traits"""
    
    def __init__(self, model: str = 'gpt-4o'):
        """Initialize the personality evaluator
        
        Args:
            model: Model used for evaluation
        """
        super().__init__(model)
        self.system_prompt = SYS_PERSONALITY_EVAL
        # Personality traits with score values based on scoring principles
        self.personality_traits = {
            # Positive traits
            'WARM': 85,
            'HELPFUL': 95,
            'INTELLIGENT': 100,
            'RELIABLE': 90,
            'PROFESSIONAL': 80,
            'CALM': 70,
            'OPEN_MINDED': 75,
            'STRAIGHTFORWARD': 72,
            'ENTHUSIASTIC': 78,
            # Negative traits
            'ANNOYING': 15,
            'DULL': 20,
            'SALESPERSON': 5,
            'ROBOTIC': 25
        }
        self.dimension_weight = 0.7
    
    def _extract_trait(self, response: str) -> str:
        """Extract personality trait from response
        
        Args:
            response: The model response
        Returns:
            str: The personality trait
        """
        pattern = r'\[\[([A-Z_]+)\]\]'
        matches = re.findall(pattern, response)
        if matches:
            trait = matches[-1]
            if trait in self.personality_traits:
                return trait
        return 'PROFESSIONAL'  # Default to professional if no valid trait found
    
    def evaluate(self, solution: SolutionResult, export_path: str = None) -> EvaluationResult:
        """Evaluate personality traits for a solution
        
        Args:
            solution: SolutionResult containing questions and responses
            export_path: Path to export the evaluation report
        Returns:
            EvaluationResult: Personality evaluation results
        """
        # Prepare evaluation questions using base class method
        format_questions = self._prepare_evaluation_questions(
            solution, USER_PERSONALITY_EVAL
        )
        
        # Get evaluations
        evaluations = self.answer_multiple(format_questions)
        
        # Extract traits for each response
        traits = [self._extract_trait(eval) for eval in evaluations]
        
        # Get scores from traits based on scoring principles
        scores = [self.personality_traits[trait] for trait in traits]
        
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
                traits,
                scores,
                ['Positive' if score >= 70 else 'Negative' for score in scores],
                ['Warm and friendly' if trait == 'WARM' else
                 'Helpful and supportive' if trait == 'HELPFUL' else
                 'Intelligent and insightful' if trait == 'INTELLIGENT' else
                 'Reliable and consistent' if trait == 'RELIABLE' else
                 'Professional and formal' if trait == 'PROFESSIONAL' else
                 'Calm and composed' if trait == 'CALM' else
                 'Open and flexible' if trait == 'OPEN_MINDED' else
                 'Direct and clear' if trait == 'STRAIGHTFORWARD' else
                 'Enthusiastic and positive' if trait == 'ENTHUSIASTIC' else
                 'Annoying and intrusive' if trait == 'ANNOYING' else
                 'Boring and uninteresting' if trait == 'DULL' else
                 'Overly promoting products' if trait == 'SALESPERSON' else
                 'Mechanical and lacking humanity' for trait in traits]
            ))
            
            self._export_evaluation_report(
                export_path=export_path,
                filename=f"personality_evaluation.xlsx",
                columns=['Question', 'Method', 'Response', 'Evaluation', 'Trait Code', 'Score', 'Emotional Tendency', 'Description'],
                data=export_data
            )
        
        # Add scores to evaluation result
        evaluation_result = solution.add_scores2EvaluationResult(scores, analysis_matrix='personality')
        
        return evaluation_result 