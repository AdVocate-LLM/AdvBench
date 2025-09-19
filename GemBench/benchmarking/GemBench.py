from typing import Callable, List, Dict, Optional
from .evaluator import QuantEvaluator, LAJQualitativeEvaluator
from .utils.struct import EvaluationResult
from .processor import Processor, SelectProcessor
from .utils.cache import ExperimentCache
import os   
from .utils.logger import ModernLogger
from .utils.struct import SolutionResult
from .dataset.GemDatasets import GemDatasets
import time

class GemBench(ExperimentCache):
    current_dir = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, 
                solutions: Optional[List[Dict[str, Callable]]]=None, 
                data_sets: Optional[List[str]]=None,
                best_product_selector: Optional[List[Dict[str, Callable]]]=None,
                judge_model: str = 'gpt-4o-mini',
                output_dir: str = current_dir,
                n_repeats: int = 1, 
                max_samples: int = 0,
                tags: str = ''
                ):
        ModernLogger.__init__(self, name="GemBench")
        ExperimentCache.__init__(self)
        self.tags = tags
        self.datasets = GemDatasets()
        if not data_sets:
            self.data_sets = self.datasets.get_all_data_set_names()
        else:
            self.data_sets = data_sets
        self.create_experiment_context()
        self.solutions = solutions
        self.best_product_selector = best_product_selector
        self._generate_insert_mode = False
        self._select_mode = False
        if solutions:
            self._generate_insert_mode = True
        if best_product_selector:
            self._select_mode = True
        self.evaluate_result = EvaluationResult()
        self.current_time = time.strftime("%Y%m%d_%H%M%S")
        self.output_dir = os.path.join(output_dir, 'output', f'{self.current_time}_{tags}')
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.judge_model = judge_model
        self.n_repeats = n_repeats
        self.max_samples = max_samples
        self.banner(
            project_name="GemBench",
            title="Welcome to GEM-Bench",
            description=(
                "- The first comprehensive benchmark for evaluating ad-injected responses (AIR) in Generative Engine Marketing (GEM),\n"
                "- Includes curated datasets across chatbot and search scenarios,\n"
                "- Provides an evaluation framework with a metric ontology for user satisfaction and engagement,\n"
                "- Supports baseline solutions within an extensible multi-agent framework."
            )
        )
        self.info(f"the judge model is: {self.judge_model}")
        self.info(f"the output directory is: {self.output_dir}")
        self.info(f"the number of repeats is: {self.n_repeats}")
        self.info(f"the maximum number of samples is: {self.max_samples if self.max_samples > 0 else 'all'}")
        self.info(f"the data sets are: {self.data_sets+["CA_Prod"] if best_product_selector else self.data_sets}")
        self.info(f"the methods we want to evaluate(chatbot task) are: {self.solutions.keys()}")
        if self.best_product_selector:
            self.info(f"the methods we want to evaluate(search task) are: {self.best_product_selector.keys()}")
        self.info("ok, let's start the evaluation!")
        
    def _get_all_evaluator(self, output_dir: str=None, results: EvaluationResult=None):
        if output_dir is None:
            output_dir = self.output_dir
        self.evaluators = {
            'QuantEvaluator': QuantEvaluator(output_dir=output_dir, results=results),
            'LAJQualitativeEvaluator': LAJQualitativeEvaluator(output_dir=output_dir, results=results, judge_model=self.judge_model)
        }
        return self.evaluators

    def process_results(self)-> SolutionResult:
        gen_results = SolutionResult()
        select_results = SolutionResult()
        # Step 1: Get the results from the solutions
        self.stage("Stage 1: Using the solutions to process the data sets")
        if self._generate_insert_mode:
            processor = Processor(
                data_sets=self.data_sets, 
                solution_models=self.solutions, 
                output_dir=self.output_dir
            )
            gen_results += processor.process(n_repeats=self.n_repeats)
        if self._select_mode:
            selector_processor = SelectProcessor(
                data_sets=self.data_sets, 
                solution_models=self.solutions, 
                output_dir=self.output_dir,
                best_product_selectors=self.best_product_selector,
            )
            select_results += selector_processor.process(n_repeats=self.n_repeats) 
        # (Optional) Save the results to the output directory as json file
        all_results = gen_results + select_results
        all_results.save(os.path.join(self.output_dir, 'results.json'))
        # (Optional) load the results from the json file
        # results = SolutionResult.load(os.path.join(self.output_dir, 'results.json'))
        # results = SolutionResult.load(os.path.join(self.output_dir, '<the path to output>/output/20250821_085337_8-20/results.json'))
        # gen_results = results.query_result_by_attr(filters={"dataSet": ["MT-Human","LM-Market"]})
        # select_results = results.query_result_by_attr(filters={"dataSet": ["CA_Prod"]})
        return gen_results, select_results
     

    def evaluate(self, 
                 gen_results:SolutionResult=SolutionResult(),
                 select_results:SolutionResult=SolutionResult(), 
                 evaluate_matrix: List[str]=None):
        self.stage("Stage 2: Base on the evaluate_mode, Let the judge model evaluate the results")
        # Step 1: basic evaluation
        all_results = gen_results + select_results
        evaluators = self._get_all_evaluator(output_dir=self.output_dir, results=all_results)
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
        
        self.evaluate_result += evaluation_result

        if len(select_results) > 0:
            from .evaluator.selector_evaluator import SelectEvaluator
            selector_evaluator = SelectEvaluator(
                output_dir=self.output_dir,
                best_product_selectors=self.best_product_selector,
                results=select_results
            )
            # Step 3: Evaluate the results
            evaluation_result = selector_evaluator.evaluate(["product_selection_accuracy"])
            self.evaluate_result += evaluation_result

        self.evaluate_result.save(os.path.join(self.output_dir, 'evaluation_result.json'))
        return self

    def report(self):
        # Step 5: Save the results to the output directory as json file
        self.evaluate_result.save_to_excel_report(os.path.join(self.output_dir,'evaluation_result.xlsx'), title=self.tags if self.tags else "Report")
        self.evaluate_result.average_by_batch().save_to_excel_report(os.path.join(self.output_dir,'evaluation_result_average.xlsx'), title=self.tags+"_average" if self.tags else "Report_average")
        
        # get with product
        result_with_product = self.evaluate_result.fliter_only_has_product()
        result_with_product.save_to_excel_report(os.path.join(self.output_dir,'evaluation_result_with_product.xlsx'), title=self.tags+"_with_product" if self.tags else "Report_with_product")
        result_with_product.average_by_batch().save_to_excel_report(os.path.join(self.output_dir,'evaluation_result_with_product_average.xlsx'), title=self.tags+"_with_product_average" if self.tags else "Report_with_product_average")
        return self

    def run(self, evaluate_matrix: List[str]=None):
        gen_results, select_results = self.process_results()
        self.evaluate(gen_results, select_results, evaluate_matrix=evaluate_matrix)
        self.report()
        return self