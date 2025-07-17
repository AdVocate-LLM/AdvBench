import json
import os
from typing import Dict, List, Tuple, Any, Callable, Optional
from collections import defaultdict
from .result import Result
from .report import Report
import pandas as pd

class SolutionResult(Dict[Tuple[str, str, str], List[Result]]):
    """
    The structure of the result:
    {
        (solution_name, dataSet, repeat_id): [Result(prompt, category, solution_tag, content, product), ...]
    }
    """

    def __init__(self) -> None:
        super().__init__()

    def add_result(
        self,
        solution_name: str,
        dataSet: str,
        repeat_id: str,
        result: Result
    ) -> "SolutionResult":
        """
        Add a Result under the specified (solution_name, dataSet, repeat_id) key.
        Initializes the list if necessary.

        Args:
            solution_name (str): the name of the solution
            dataSet (str): the name of the dataSet
            repeat_id (str): the repeat identifier
            result (Result): the Result object to add
        """
        key = (solution_name, dataSet, repeat_id)
        self.setdefault(key, []).append(result)
        return self
    
    def __add__(self, other: "SolutionResult") -> "SolutionResult":
        """
        Return a new SolutionResult containing entries from both self and other.
        Does not modify the originals.
        """
        merged = SolutionResult()
        # copy self
        for key, results in self.items():
            merged[key] = list(results)
        # merge other
        for key, results in other.items():
            merged.setdefault(key, []).extend(results)
        return merged

    def __iadd__(self, other: "SolutionResult") -> "SolutionResult":
        """
        In-place merge of other into self.
        """
        for key, results in other.items():
            self.setdefault(key, []).extend(results)
        return self
    
    def get_all_results(self) -> List[Result]:
        """
        Get all the results of the SolutionResult.
        """
        return [result for results in self.values() for result in results]
    
    def _to_matrix(self)->List[Tuple[str,str,str,str,str,str,str,str]]:
        """
        Convert SolutionResult to matrices
        
        Return: List[Tuple[str,str,str,str,str,str,str,str]]
        - 0: solution_name
        - 1: data_set
        - 2: repeat_id
        - 3: prompt
        - 4: category
        - 5: tag
        - 6: raw_answer
        - 7: product 
        """
        matrices=[]
        
        for item in self.items():
            for result in item[1]:
                matrices.append(
                    (
                        item[0][0],                # solution_name
                        item[0][1],                # data_set
                        item[0][2],                # repeat_id
                        result.get_prompt(),       # prompt
                        result.get_category(),     # category
                        result.get_solution_tag(), # tag
                        result.get_raw_response(), # raw_answer
                        result.get_product()       # product
                    )
                )
        
        return matrices
        
    def add_list_of_results(
        self,
        solution_name: str,
        dataSet: str,
        repeat_id: str,
        results: List[Result]
    ) -> "SolutionResult":
        """
        Add a list of Result objects to the SolutionResult.
        
        Args:
            solution_name (str): the name of the solution
            dataSet (str): the name of the dataSet
            repeat_id (str): the repeat identifier
            results (List[Result]): the list of Result objects to add
        """
        key = (solution_name, dataSet, repeat_id)
        self.setdefault(key, []).extend(results)
        return self

    def query_result_by_attr(
        self,
        filters: Dict[str, List[str]]
    ) -> "SolutionResult":
        """
        Return a new SolutionResult filtered by any of:
        'solution_name', 'dataSet', 'repeat_id'.
        """
        result = SolutionResult()
        for (sol, ds, rid), lst in self.items():
            if "solution_name" in filters and sol not in filters["solution_name"]:
                continue
            if "dataSet" in filters and ds not in filters["dataSet"]:
                continue
            if "repeat_id" in filters and rid not in filters["repeat_id"]:
                continue
            result[(sol, ds, rid)] = list(lst)
        return result
    
    def get_result_group_by_attrs(self, attrs: List[str]) -> Dict[Tuple[str, ...], List[Result]]:
        """
        Group the results by the specified attributes.
        
        Args:
            attrs (List[str]): List of attributes to group by, can include 'solution_name', 'dataSet', 'repeat_id'
            
        Returns:
            Dict[Tuple[str, ...], List[Result]]: Dictionary with keys as tuples of attribute values and values as lists of Result objects
        
        Example of usage:
        result = SolutionResult()
        result.group_by_attrs(['solution_name', 'dataSet'])
        {
            ('sol1', 'ds1'): [Result, ...], 
            ('sol2', 'ds2'): [Result, ...]
            ...
        }
        """
        grouped_results = {}
        
        for (sol, ds, rid), results in self.items():
            key_values = []
            for attr in attrs:
                if attr == "solution_name":
                    key_values.append(sol)
                elif attr == "dataSet":
                    key_values.append(ds)
                elif attr == "repeat_id":
                    key_values.append(rid)
            
            key = tuple(key_values)
            
            if key not in grouped_results:
                grouped_results[key] = []
            grouped_results[key].extend(results)
            
        return grouped_results        
    
    def group_by_attrs(self, attrs: List[str]) -> Dict[Tuple[str, ...], "SolutionResult"]:
        """
        Group this SolutionResult by the specified attributes.

        Args:
            attrs (List[str]): List of attributes to group by.
                Valid values are 'solution_name', 'dataSet', 'repeat_id'.

        Returns:
            Dict[Tuple[str, ...], SolutionResult]: A dict mapping each group key (tuple of attribute values)
            to a SolutionResult containing only the results in that group.

        Example:
            groups = self.group_by_attrs(['solution_name', 'dataSet'])
            # e.g. {('solA', 'ds1'): SolutionResult(...), ...}
        """
        grouped: Dict[Tuple[str, ...], SolutionResult] = {}

        for (sol, ds, rid), results in self.items():
            # build tuple key based on attrs
            key_parts: List[str] = []
            for attr in attrs:
                if attr == "solution_name":
                    key_parts.append(sol)
                elif attr == "dataSet":
                    key_parts.append(ds)
                elif attr == "repeat_id":
                    key_parts.append(rid)
                else:
                    raise ValueError(f"Unsupported attribute for grouping: {attr!r}")
            key = tuple(key_parts)

            # initialize group if needed
            if key not in grouped:
                grouped[key] = SolutionResult()

            # add each Result into the appropriate SolutionResult
            for result in results:
                grouped[key].add_result(sol, ds, rid, result)

        return grouped
        
    def get_keys_by_attr(self, attr: str) -> List[str]:
        """
        Collect all unique values for one of:
        'solution_name', 'dataSet', 'repeat_id'
        """
        idx_map = {"solution_name": 0, "dataSet": 1, "repeat_id": 2}
        idx = idx_map.get(attr)
        if idx is None:
            return []
        return list({key[idx] for key in self.keys()})
    
    def save(self, file_path: str) -> None:
        """
        Save the SolutionResult to a JSON file.
        
        Args:
            file_path (str): Path to save the JSON file
        """
        import json
        import os
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Convert to serializable format
        serializable_data = {}
        for (solution_name, dataSet, repeat_id), results in self.items():
            key = f"{solution_name}|{dataSet}|{repeat_id}"
            serializable_data[key] = [result.to_json() for result in results]
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, file_path: str) -> "SolutionResult":
        """
        Load a SolutionResult from a JSON file.
        
        Args:
            file_path (str): Path to the JSON file
            
        Returns:
            SolutionResult: The loaded SolutionResult object
        """
        import json
        from benchmarking.utils.result import Result
        
        solution_result = cls()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            serialized_data = json.load(f)
        
        for key, result_list in serialized_data.items():
            solution_name, dataSet, repeat_id = key.split('|')
            repeat_id = int(repeat_id)  # Convert repeat_id to integer
            
            for result_data in result_list:
                result = Result(
                    prompt=result_data.get('prompt', ''),
                    category=result_data.get('category', ''),
                    solution_tag=result_data.get('solution', ''),
                    content=result_data.get('content', ''),
                    product=result_data.get('product', '')
                )
                # Set additional attributes from the JSON
                result.raw_content = result_data.get('content', '')
                result.logprobs = result_data.get('logprobs', None)
                result.product = result_data.get('product', None)
                
                solution_result.add_result(
                    solution_name=solution_name, 
                    dataSet=dataSet, 
                    repeat_id=str(repeat_id), 
                    result=result
                )
        
        return solution_result
    
    def self_evaluated_with_matrix_by_fn(
        self,
        evaluator_fn: Callable[[Result], float],
        eval_matrix_label: str
    ) -> "EvaluationResult":
        """
        Evaluate each stored Result using evaluator_fn and collect scores.
        Notice that the evaluator_fn is a function that takes a Result and returns a float score.
        And this function is only used for self-evaluation,
        !!!!!SO, YOU CANNOT USE THIS FUNCTION FOR COMPARATIVE EVALUATION!!!!!!

        Args:
            evaluator_fn (Callable[[Result], float]): Function that takes a Result and returns a float score.
            eval_matrix_label (str): Label for the evaluation matrix to record.

        Returns:
            EvaluationResult: Mapping of (solution_name, dataSet, repeat_id, eval_matrix_label, category) to score.
        """
        # Import EvaluationResult to record scores
        eval_results = EvaluationResult()
        # Iterate over all solution entries
        for (solution_name, dataSet, repeat_id), result_list in self.items():
            for res in result_list: # type of res: Result
                # Compute score for each individual Result
                score = evaluator_fn(res)
                if score is None:
                    if eval_matrix_label == "has_ad":
                        score = 0
                    else:
                        continue
                eval_results.add_result(
                    solution_name,
                    dataSet,
                    repeat_id,
                    eval_matrix_label,
                    res.get_category(),
                    float(score)
                )
        return eval_results

    def add_scores2EvaluationResult(
        self,
        scores: List[float],
        analysis_matrix: str = "evaluation"
    ) -> "EvaluationResult":
        """
        Add a list of scores to the EvaluationResult.
        This function is used to add the scores of the evaluation result to the EvaluationResult.
        
        Args:
            scores: List[float] - List of scores corresponding to each result in the SolutionResult
            analysis_matrix: str - The evaluation matrix label (default: "evaluation")

        Returns:
            EvaluationResult: The EvaluationResult object with the added scores.
        """
        evaluation_result = EvaluationResult()
        
        # Get all items as a flat list to match with scores
        matrices = self._to_matrix()
        
        # Check if scores length matches the number of results
        if len(scores) != len(matrices):
            raise ValueError(f"Number of scores ({len(scores)}) doesn't match number of results ({len(matrices)})")
        
        # Add each score to the evaluation result
        for score, matrix in zip(scores, matrices):
            solution_name = matrix[0]
            dataset = matrix[1]
            repeat_id = matrix[2]
            category = matrix[4]
            
            evaluation_result.add_result(
                solution_name, 
                dataset, 
                repeat_id, 
                analysis_matrix, 
                category, 
                float(score)
            )
        
        return evaluation_result


class EvaluationResult(List[Tuple[Tuple[str, str, str, str, str], float]]):
    """
    The structure of the evaluation result:
    Structure:
        [
            ((solution_name, dataSet, repeat_id, analysis_matrix, category), float),
            ...
        ]
    """
    def add_result(
        self,
        solution_name: str,
        dataSet: str,
        repeat_id: str,
        analysis_matrix: str,
        category: str,
        result: float
    ) -> None:
        """
        Add a new result to the EvaluationResult.
        If the key exists, its value must not be replaced.
        We must keep all the results.
        """
        key = (solution_name, dataSet, repeat_id, analysis_matrix, category)
        # Append new result
        self.append((key, result))

    def __add__(self, other: "EvaluationResult") -> "EvaluationResult":
        """
        Merge two EvaluationResult objects.
        We do not remove existing entries with the same key.
        Because we want to keep all the results.
        """
        merged = EvaluationResult()
        merged.extend(self)
        merged.extend(other)
        return merged

    def __iadd__(self, other: "EvaluationResult") -> "EvaluationResult":
        """
        In-place addition: merge entries from other into self.
        """
        for k, v in other:
            self.add_result(*k, v)
        return self

    def query_result_by_attr(
        self,
        filters: Dict[str, List[str]]
    ) -> "EvaluationResult":
        """
        Query the results by specified attribute filters.
        """
        idx_map = {
            "solution_name": 0,
            "dataSet": 1,
            "repeat_id": 2,
            "analysis_matrix": 3,
            "category": 4,
        }
        result = EvaluationResult()
        for key, val in self:
            if any(key[idx_map[attr]] not in vals for attr, vals in filters.items()):
                continue
            result.append((key, val))
        return result

    def get_average_result_by_attr(
        self,
        filters: Dict[str, List[str]]
    ) -> float:
        """
        Get the average of results matching the given filters.
        """
        filtered = self.query_result_by_attr(filters)
        if not filtered:
            return 0.0
        return sum(val for _, val in filtered) / len(filtered)

    def get_keys_by_attr(self, attr: str) -> List[str]:
        """
        Collect all unique keys for the specified attribute.
        """
        idx_map = {
            "solution_name": 0,
            "dataSet": 1,
            "repeat_id": 2,
            "analysis_matrix": 3,
            "category": 4,
        }
        idx = idx_map.get(attr)
        if idx is None:
            return []
        return list({key[idx] for key, _ in self})

    def group_by_attr(self, attr: str) -> Dict[str, "EvaluationResult"]:
        """
        Group the results by the specified attribute.
        """
        return {
            val: self.query_result_by_attr({attr: [val]})
            for val in self.get_keys_by_attr(attr)
        }

    def to_dict_report(self, output_dir: Optional[str]=None) -> Dict[str, Any]:
        """
        Convert flat list into nested dictionary report with averages (__all__ entries).
        """
        report: Dict[str, Any] = {}

        # Build bottom-level nesting
        for (sol, ds, run, mat, _), score in self:
            # compute average for this cell
            value = self.get_average_result_by_attr({
                "solution_name":  [sol],
                "dataSet":        [ds],
                "repeat_id":      [run],
                "analysis_matrix":[mat]
            })
            # ensure it's a built-in float, not numpy.float32
            report.setdefault(ds, {}) \
                .setdefault(sol, {}) \
                .setdefault(run, {})[mat] = float(value)

        # Average across runs for each (ds, sol)
        for ds, sols in report.items():
            for sol, runs in sols.items():
                metric_vals: Dict[str, List[float]] = defaultdict(list)
                for run, metrics in runs.items():
                    for m, v in metrics.items():
                        metric_vals[m].append(v)
                runs["__all__"] = {m: float(sum(vals) / len(vals)) for m, vals in metric_vals.items()}

        # Average per solution within each dataset
        for ds, sols in report.items():
            sol_avg: Dict[str, float] = {}
            for sol, runs in sols.items():
                if sol == "__all__":
                    continue
                vals = [
                    v
                    for run, metrics in runs.items() if run != "__all__"
                    for v in metrics.values()
                ]
                sol_avg[sol] = float(sum(vals) / len(vals)) if vals else 0.0
            report[ds]["__all__"] = sol_avg

        # Top-level average across datasets
        top_avg: Dict[str, float] = {}
        for ds, sols in report.items():
            if ds == "__all__":
                continue
            vals = [
                v
                for sol, runs in sols.items() if sol != "__all__"
                for run, metrics in runs.items() if run != "__all__"
                for v in metrics.values()
            ]
            top_avg[ds] = float(sum(vals) / len(vals)) if vals else 0.0
        report["__all__"] = top_avg
        
        # (Optional)save report to json
        if output_dir is not None:
            os.makedirs(os.path.dirname(output_dir), exist_ok=True)
            with open(os.path.join(os.path.dirname(output_dir), "report.json"), "w") as f:
                json.dump(report, f, indent=4)

        return report

    def save_to_excel_report(self, file_path: str) -> None:
        """
        Save the nested report into an Excel file using a Report utility.
        """
        report_dict = self.to_dict_report(file_path)

        # Flatten for DataFrame
        records: List[Dict[str, Any]] = []
        for ds, sols in report_dict.items():
            if ds == "__all__":
                continue
            for sol, runs in sols.items():
                if sol == "__all__":
                    continue
                for run, metrics in runs.items():
                    if run == "__all__":
                        continue
                    rec = {"data_set": ds, "solution": sol, "run": run}
                    rec.update(metrics)
                    records.append(rec)
        df = pd.DataFrame(records)
        
        # Check if DataFrame is empty
        if df.empty:
            print("Warning: No evaluation results to save. Creating empty Excel file.")
            # Create empty Excel file with basic structure
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                empty_df = pd.DataFrame(columns=['data_set', 'solution', 'run'])
                empty_df.to_excel(writer, sheet_name='Results', index=False)
            return
        
        # Step 4: Configure the Excel report settings
        metric_config = {}
        all_metrics = [col for col in df.columns if col not in ['data_set', 'solution', 'run']]
        
        # "compare" group
        compare_metrics = ["better", "worse", "same"]
        # "global measure" group
        global_measure_metrics = ["ad_content_alignment", "ad_transition_similarity"]
        # "local measure" group
        local_measure_metrics = ["local_flow", "global_coherence"]
        
        assigned_metrics = set()
        
        for metric in all_metrics:
            if metric in compare_metrics:
                metric_config[metric] = "compare"
                assigned_metrics.add(metric)
            elif metric in global_measure_metrics:
                metric_config[metric] = "global measure"
                assigned_metrics.add(metric)
            elif metric in local_measure_metrics:
                metric_config[metric] = "local measure"
                assigned_metrics.add(metric)
        
        for metric in all_metrics:
            if metric not in assigned_metrics:
                metric_config[metric] = ""
        
        # Required columns in the specified order
        required_columns = ['data_set', 'solution', 'run']
        
        # Define color scheme
        color_scheme = {
            'title': {
                'font_color': 'FFFFFF',
                'fill_color': '42B883'      
            },
            'header_level1': {
                'font_color': 'FFFFFF',
                'fill_color': '3490DC'      
            },
            'header_level2': {
                'font_color': 'FFFFFF',
                'fill_color': '6574CD'      
            },
            'dataset_highlight': '35495E', 
            'max_value_highlight': '4CAF50',
            'row_colors': {
                'default': 'FFFFFF'         
            }
        }

        unique_datasets = df['data_set'].unique()
        dataset_gradient = ['42B883', '49A5A5', '5A6ED0', '6574CD']
        dataset_colors = dataset_gradient[: len(unique_datasets)]

        for i, ds in enumerate(unique_datasets):
            color_idx = i % len(dataset_colors)  # Cycle through colors if more datasets than colors
            color_scheme['row_colors'][ds] = dataset_colors[color_idx]
        
        # Step 5: Generate the Excel report
        report = Report(
            df=df,
            output_file=file_path,
            metric_config=metric_config,
            required_columns=required_columns,
            color_scheme=color_scheme
        )
        report.create_report_excel()
