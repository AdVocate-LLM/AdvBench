from typing import List, Dict, Callable
from .processor import Processor
from benchmarking.dataset import AdvDatasets
from benchmarking.utils.result import Result
from benchmarking.utils.struct import SolutionResult

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
    dataset = AdvDatasets()

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
        # Get solution function and best product selector
        best_product_selector_fn = self.get_best_product_selector(solution_name)
        
        # Combine results with best product information
        results = []
        prompt_list = self.dataset.get_query_list()
        problem_product_list, query_clusters = self.dataset.build_query_candidate_product_list()
        
        # Call the best product selector with the problem_product_list
        best_product_lists = best_product_selector_fn(
            problem_product_list=problem_product_list,
        )
        
        if isinstance(best_product_lists, dict):
        # Process results for each query
            for prompt, best_product in best_product_lists.items():  
                results.append(
                    Result(
                        prompt=prompt,
                        category=best_product['category'],
                        solution_tag=solution_name,
                        content=f"{best_product['name']}--{best_product['description']}",
                        product={
                            "name": best_product['name'],
                            "description": best_product['description'],
                            "url": best_product['url'],
                            "category": best_product['category']
                        }
                    )
                )
        
        # Create solution result
        solution_result = SolutionResult()
        
        # Add results to solution result
        solution_result.add_list_of_results(
            solution_name=solution_name,
            dataSet=data_name,
            repeat_id=str(repeat_id),
            results=results
        )
        
        # Save results if requested
        if is_saved:
            output_path = self.get_store_path_for_solution_dataset_repeat(solution_name, data_name, repeat_id)    
            result_file_path = output_path + '/result.json'
            # Save the result
            solution_result.save(result_file_path)
            self.info(f"Results saved to: {result_file_path}")

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
        print(solutions)
        for solution_name in solutions:
            self.section(f"Using {solution_name} to process the data sets...")
            results += self.process_repeat(
                data_name="best_product_selector", 
                solution_name=solution_name, 
                n_repeats=n_repeats, 
                max_samples=max_samples, 
                is_saved=is_saved)
        return results