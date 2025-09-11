from typing import List
from ..utils.struct import SolutionResult, EvaluationResult
from ..utils.path import Path
from ..utils.parallel import ParallelProcessor
from abc import ABC, abstractmethod
from ..utils.logger import ModernLogger

class BaseEvaluator(Path,ABC,ParallelProcessor,ModernLogger):
    def __init__(self, output_dir: str, results: SolutionResult=SolutionResult()):
        """
        Initialize the BaseEvaluator.

        Args:
            output_dir (str): The root output directory.
            results (EvaluationResult): The results to save.
        """
        Path.__init__(self,output_dir=output_dir)
        ABC.__init__(self)
        ModernLogger.__init__(self,name="Evaluator")
        ParallelProcessor.__init__(self)
        self.results = results # {solution_name: [{dataSet: [{repeat_id: [Result]}]}}
        self.merged_results = {} 
        
    @abstractmethod
    def get_analysis_matrixes(self) -> List[str]:
        """
        Get the analysis matrixes.
        
        Returns:
            List[str]: The all of the analysis matrixes the evaluator can provide.
        
        Abstract Method: we need to implement this method in the subclass.
        """
        pass
    
    @abstractmethod
    def evaluate(self, analysis_matrixes: List[str]=None, is_saved: bool = True) -> EvaluationResult:
        """
        Evaluate the result.
        
        Args:
            analysis_matrixes (List[str]): The analysis matrixes to evaluate.
            is_saved (bool): Whether to save the result.
        Returns:
            EvaluationResult: The evaluated result.
        Abstract Method: we need to implement this method in the subclass.
        """
        pass