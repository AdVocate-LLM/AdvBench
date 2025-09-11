from typing import List, Dict, Callable
from ..dataset import GemDatasets
from ..utils.result import Result
from ..utils.path import Path
import os
import random
from ..utils.struct import SolutionResult
from ..utils.logger import ModernLogger
from ..utils.cache import ExperimentCache

class Processor(Path, GemDatasets, ExperimentCache):
    """
    Processor class for processing the data sets and solutions

    Args:
        data_sets (List[str]): the names of the data sets
        solution_model (Dict[str, Callable]): the solution models
        output_dir (str): the output directory
        data_set_names (List[str], optional): specific dataset names to use. Defaults to None.
    
    Design:
        data_sets
        |-- solution_model
        |   |-- output_dir
        |   |   |-- result.json
        |   |   |-- result.json
    """

    def __init__(
        self, data_sets: List[str], 
            solution_models: Dict[str, Callable],
            output_dir: str,
            ):
        """
        Initialize the Processor

        Args:
            data_sets (List[str]): the names of the data sets
            solution_model (Dict[str, Callable]): the solution models
            output_dir (str): the output directory
            data_set_names (List[str], optional): specific dataset names to use. Defaults to None.

        Raises:
            ValueError: if the data_sets is not a list of valid dataset names
            ValueError: if the solution_model is not a dictionary of valid solution names
            ValueError: if the output_dir is not a valid directory
        """
        # Initialize parent classes
        Path.__init__(self, output_dir=output_dir)
        GemDatasets.__init__(self, data_set_names=data_sets)
        ModernLogger.__init__(self, name="Processor")
        ExperimentCache.__init__(self)

        # check if the data_sets is a list of valid dataset names
        for data_name in data_sets:
            if data_name not in self.get_data_set_names():
                raise ValueError(f"Invalid dataset name: {data_name}")
        
        # check if the output_dir is a valid directory
        if not os.path.exists(output_dir):
            raise ValueError(f"Invalid output directory: {output_dir}")
                
        self.data_sets = data_sets
        self.solution_models = solution_models
        self.output_dir = output_dir
    
    def get_solution_names(self):
        """
        Get the solution names
        Returns:
            List[str]: the solution names
        """
        return list(self.solution_models.keys())
        
    def get_solution_model(self, solution_name: str):
        """
        Get the solution model for a given solution name
        Args:
            solution_name (str): the name of the solution
        Returns:
            Callable: the solution model
        """
        return self.solution_models[solution_name]
    
    
    def call_solution_model(
        self, 
        data_name: str, 
        solution_name: str, 
        repeat_id: int, 
        max_samples: int = 0, 
        is_saved: bool = True)->SolutionResult:
        """
        Call the solution model for a given data set and solution name
        """
        # get result
        solution_fn = self.get_solution_model(solution_name)
        
        # get dataset
        prompt_list = self.get_prompt_list(data_name)
        if max_samples > 0:
            prompt_list = random.sample(prompt_list, max_samples)
        category_list = self.get_categories_list(data_name)
        category = category_list[0]
        solution_result = SolutionResult()
        raw_result = solution_fn(problem_list=prompt_list)
        # Filter out results where answer is None
        valid_results = []
        error_results = []
        
        for result in raw_result:
            if result is not None and result['answer'] is not None:
                valid_results.append(
                    Result(
                        prompt=result['query'],
                        category=category,
                        solution_tag=solution_name,
                        raw_content=result['answer'],
                        product=result['product'],
                        price=result['price']
                    )
                )
            else:
                error_results.append({
                    'prompt': result['query'],
                    'category': category,
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
    
    def process_repeat(
        self, data_name: str, 
        solution_name: str, 
        n_repeats: int = 1, 
        max_samples: int = 0, 
        is_saved: bool = True)->SolutionResult:
        """
        Process the data for a given data set and solution name
        Args:
            data_name (str): the name of the data set
            solution_name (str): the name of the solution
            n_repeats (int): the number of repeats
            save_n_load (bool): whether to save the results
            num_workers (int): the number of workers
            max_samples (int): the maximum number of samples
            is_parallel (bool): whether to run in parallel
            is_saved (bool): whether to save the results
        Returns: 
        """
        results = SolutionResult()
        for repeat_id in range(n_repeats):
            self.update_experiment_context(current_batch=repeat_id)
            results += self.call_solution_model(
                data_name=data_name, 
                solution_name=solution_name, 
                repeat_id=repeat_id, 
                max_samples=max_samples, 
                is_saved=is_saved
                )
        return results
    
    def process_dataset(
            self,
            solutions: str, 
            data_sets: List[str],
            n_repeats: int = 1,  
            max_samples: int = 0, 
            is_saved: bool = True
        )->SolutionResult:
        """
        Process the data for a given data set and solution name
        Args:
            data_name (str): the name of the data set
            solutions (List[str]): the names of the solutions
        Returns:
            SolutionResult: The result of the solutions
        """
        results = SolutionResult()
        for data_name in data_sets:
            results += self.process_repeat(
                data_name=data_name, 
                solution_name=solutions, 
                n_repeats=n_repeats, 
                max_samples=max_samples, 
                is_saved=is_saved)
        return results
        
    
    def process(
            self, 
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
        data_sets = self.get_data_set_names()
        solutions = self.get_solution_names()
        results = SolutionResult()
        for solution_name in solutions:
            self.section(f"Using {solution_name} to process the data sets...")
            results += self.process_dataset(
                solutions=solution_name, 
                data_sets=data_sets, 
                n_repeats=n_repeats, 
                max_samples=max_samples, 
                is_saved=is_saved)


        # filter the result of each query should be contain all answer categories
        # if not, add remove the result of the query
        results = self.filter_result_for_comparison(results).embedding_all_results()
        return results
    
    def filter_result_for_comparison(self, results: SolutionResult) -> SolutionResult:
        """
        Filter results to ensure each query has results from all solution methods.
        If a query doesn't have results from all methods, remove all results for that query.
        """
        # Get all unique solution names
        all_solutions = set(results.get_keys_by_attr("solution_name"))
        
        # Group by dataset and repeat_id, then check query completeness within each group
        filtered_results = SolutionResult()
        
        # Group by dataset and repeat_id
        dataset_repeat_groups = results.group_by_attrs(["dataSet", "repeat_id"])
        
        for (dataset, repeat_id), group_results in dataset_repeat_groups.items():
            # Within this dataset+repeat group, check query completeness
            query_solution_map = {}
            
            # Build map of query -> set of solutions
            for result in group_results.get_all_results():
                query = result.prompt
                solution = result.solution_tag
                
                if query not in query_solution_map:
                    query_solution_map[query] = set()
                query_solution_map[query].add(solution)
            
            # Find valid queries that have all solutions
            valid_queries = {
                query for query, solutions in query_solution_map.items() 
                if solutions == all_solutions
            }
            
            # Add only valid results to filtered_results
            for (solution_name, ds, rid), result_list in group_results.items():
                valid_result_list = [r for r in result_list if r.prompt in valid_queries]
                if valid_result_list:
                    filtered_results.add_list_of_results(
                        solution_name=solution_name,
                        dataSet=ds,
                        repeat_id=rid,
                        results=valid_result_list
                    )
        
        original_count = len(results.get_all_results())
        filtered_count = len(filtered_results.get_all_results())
        self.info(f"Filtered from {original_count} to {filtered_count} results")
        
        return filtered_results

