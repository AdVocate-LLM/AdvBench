import json
from typing import Callable, List, Dict
from benchmarking.evaluator import QuantEvaluator, LAJQualitativeEvaluator
from .utils.struct import EvaluationResult
from .processor import Processor
import os   
from .utils.logger import ModernLogger
from .utils.struct import SolutionResult

class AdvBench(ModernLogger):
    current_dir = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, 
                data_sets: List[str],
                solutions: List[Dict[str, Callable]], # 
                judge_model: str = 'gpt-4o-mini',
                output_dir: str = current_dir,
                n_repeats: int = 1, 
                max_samples: int = 0):
        super().__init__(name="AdvBench")
        self.data_sets = data_sets
        self.solutions = solutions
        self.output_dir = os.path.join(output_dir, 'output')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.judge_model = judge_model
        self.n_repeats = n_repeats
        self.max_samples = max_samples
        self.banner(
            project_name="AdvBench",
            title="Welcome to our evaluation system",
            description=(
                "- This is a evaluation system that can evaluate the quality of Adversarial LLM responses with multiple metrics,\n"
                "- Includes high-quality benchmark datasets, evaluation frameworks,\n"
                "- And configurable ad injection strategies."
            )
        )
        self.info(f"the judge model is: {self.judge_model}")
        self.info(f"the output directory is: {self.output_dir}")
        self.info(f"the number of repeats is: {self.n_repeats}")
        self.info(f"the maximum number of samples is: {self.max_samples}")
        self.info(f"the data sets are: {self.data_sets}")
        self.info("ok, let's start the evaluation!")
        
    def _get_all_evaluator(self, output_dir: str=None, results: EvaluationResult=None):
        if output_dir is None:
            output_dir = self.output_dir
        self.evaluators = {
            'QuantEvaluator': QuantEvaluator(output_dir=output_dir, results=results),
            'LAJQualitativeEvaluator': LAJQualitativeEvaluator(output_dir=output_dir, results=results, judge_model=self.judge_model)
        }
        return self.evaluators        

    def evaluate(self, output_dir: str=None, evaluate_matrix: List[str]=None):
        # Step 1: Get the results from the solutions
        
        self.stage("Stage 1: Using the solutions to process the data sets")
        processor = Processor(
            data_sets=self.data_sets, 
            solution_models=self.solutions, 
            output_dir=self.output_dir
        )
        results = processor.process()
        
        # (Optional) Save the results to the output directory as json file
        results.save(os.path.join(self.output_dir, 'results.json'))
        
        # # (Optional) load the results from the json file
        # results = SolutionResult.load(os.path.join(self.output_dir, 'results.json'))
        
        self.stage("Stage 2: Base on the evaluate_mode, Let the judge model evaluate the results")
        evaluators = self._get_all_evaluator(output_dir=output_dir, results=results)
        
        # Step 3: Group the evaluate_matrix by the evaluator
        evaluator_matrix_map = {}

        if evaluate_matrix is not None:
            for matrix_name in evaluate_matrix:
                for evaluator in evaluators.values():
                    if matrix_name in evaluator.get_analysis_matrixes():
                        if evaluator not in evaluator_matrix_map:
                            evaluator_matrix_map[evaluator] = []
                        evaluator_matrix_map[evaluator].append(matrix_name)
        else:
            for evaluator in evaluators.values():
                evaluator_matrix_map[evaluator] = evaluator.get_analysis_matrixes()

        # Step 4: Evaluate the results
        evaluation_result = EvaluationResult()
        for evaluator, matrix_names in evaluator_matrix_map.items():
            evaluation_result += evaluator.evaluate(matrix_names)
        
        # Step 5: Save the results to the output directory as json file
        evaluation_result.save_to_excel_report(os.path.join(self.output_dir, 'evaluation_result.xlsx'))
        
        return evaluation_result

