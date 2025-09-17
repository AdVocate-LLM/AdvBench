from typing import List, Dict, Callable
from .processor import Processor
from ..dataset import GemDatasets
from ..utils.result import Result
from ..utils.struct import SolutionResult

class SelectProcessor(Processor):
    """
    SelectProcessor class for processing the data sets and best product selector solutions

    Args:
        data_sets (List[str]): the names of the data sets
        solution_model (Dict[str, Callable]): the solution models
        best_product_selectors (Dict[str, Callable]): the best product selector functions
        output_dir (str): the output directory
    
    Design:
        data_sets
        |-- solution_model
        |   |-- output_dir
        |   |   |-- result.json
        |   |   |-- result.json
    """
    # dataset
    dataset = GemDatasets()

    def __init__(
        self, 
        data_sets: List[str], 
        solution_models: Dict[str, Callable],
        best_product_selectors: Dict[str, Callable],
        output_dir: str,
        ):
        """
        Initialize the SelectProcessor inherit from Processor
        """
        # Initialize parent class
        super().__init__(data_sets=data_sets, solution_models=solution_models, output_dir=output_dir)
        # Store best product selectors
        self.best_product_selectors = best_product_selectors
       
    def get_best_product_selector(self, solution_name: str):
        """
        Get the best product selector function for a given solution name
        
        Args:
            solution_name (str): the name of the solution
            
        Returns:
            Callable: the best product selector function
        """
        return self.best_product_selectors[solution_name]

    def _get_candidate_products_for_query(self, query: str):
        """
        Get the candidate products for a given query
        and the query type(cluster of query)
        """
        return self.dataset.get_candidate_product_by_query(query)
    
    def call_solution_model(
        self, 
        data_name: str, 
        solution_name: str, 
        repeat_id: int, 
        max_samples: int = 0, 
        is_saved: bool = True) -> SolutionResult:
        """
        Call the solution model for a given data set and solution name,
        with enhanced functionality for best product selection
        
        Args:
            data_name (str): the name of the data set
            solution_name (str): the name of the solution
            repeat_id (int): the repeat identifier
            max_samples (int): maximum number of samples to process (0 for all)
            is_saved (bool): whether to save the results
            
        Returns:
            SolutionResult: the solution result with best product information
        """
        # get result
        solution_fn = self.get_best_product_selector(solution_name)
        
        solution_result = SolutionResult()
        problem_product_list, query_clusters = self.dataset.build_query_candidate_product_list()
        
        # Call the best product selector with the problem_product_list
        raw_result = solution_fn(
            problem_list=problem_product_list,
        )
        # Filter out results where answer is None
        valid_results = []
        error_results = []
        
        for result in raw_result:
            if result is not None and result['answer'] is not None:
                valid_results.append(
                    Result(
                        prompt=result['query'],
                        category=result['product']["category"],
                        solution_tag=solution_name,
                        raw_content=result['answer'],
                        product=result['product'],
                        price=result['price']
                    )
                )
            else:
                error_results.append({
                    'prompt': result['query'],
                    'category': result['product']["category"],
                    'solution_tag': solution_name,
                    'error': 'No answer generated',
                    'product': result['product']
                })
        
        solution_result.add_list_of_results(
            solution_name=solution_name,
            dataSet=data_name,
            repeat_id=str(repeat_id),
            results=valid_results
        )
        
        # Save error results if any
        if error_results:
            output_path = self.get_store_path_for_solution_dataset_repeat(solution_name, data_name, repeat_id)    
            error_file_path = output_path + '/errors.json'
            import json
            import os
            os.makedirs(output_path, exist_ok=True)
            with open(error_file_path, 'w') as f:
                json.dump(error_results, f, indent=2)
            
        if is_saved:
            output_path = self.get_store_path_for_solution_dataset_repeat(solution_name, data_name, repeat_id)    
            result_file_path = output_path + '/result.json'
            # save the result
            solution_result.save(result_file_path)

        return solution_result
    
    def get_solution_names(self):
        """
        Get the names of the solutions
        """
        return list(self.best_product_selectors.keys())

    def process(
            self, 
            data_sets: List[str]=None, 
            solutions: List[str]=None, 
            n_repeats: int = 1, 
            max_samples: int = 0, 
            is_saved: bool = True
        )->SolutionResult:
        """
        Process the data for a given data set and solution name
        Args:
            data_sets (List[str]): the names of the data sets
            solutions (List[str]): the names of the solutions
        Returns:
            SolutionResult: The result of the solutions
        """
        results = SolutionResult()
        if solutions is None:
            solutions = self.get_solution_names()
        for solution_name in solutions:
            self.section(f"Using {solution_name} to process the data sets...")
            results += self.process_repeat(
                data_name="CA_Prod", 
                solution_name=solution_name, 
                n_repeats=n_repeats, 
                max_samples=max_samples, 
                is_saved=is_saved)
            
        results = self.filter_result_for_comparison(results).embedding_all_results()
        return results