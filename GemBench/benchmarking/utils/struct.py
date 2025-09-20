import json
import os
from typing import Dict, List, Tuple, Any, Callable, Optional
import matplotlib.pyplot as plt
from collections import defaultdict
from .functions import SentenceEmbedding
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

    def embedding_all_results(self) -> "SolutionResult":
        """
        Embed all the results in the SolutionResult.
        """
        # extract all the results from the value of the SolutionResult
        results = [result for results in self.values() for result in results]
        # extract raw_content from each result
        raw_contents = [result.raw_content for result in results]
        # embed all the results
        sentence_embedding = SentenceEmbedding(raw_contents)
        List_of_sentences = sentence_embedding.embed()
        # update the results
        idx = 0
        for result_list in self.values():
            for res in result_list:
                res.update_content(List_of_sentences[idx])
                idx += 1
        return self
        
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
        from GemBench.benchmarking.utils.result import Result
        
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
                    raw_content=result_data.get('content', ''),
                    product=result_data.get('product', ''),
                    price=result_data.get('price', {'in_token': 0, 'out_token': 0, 'price': 0})
                )
                # Set additional attributes from the JSON
                result.logprobs = result_data.get('logprobs', None)
                
                solution_result.add_result(
                    solution_name=solution_name, 
                    dataSet=dataSet, 
                    repeat_id=str(repeat_id), 
                    result=result
                )
        
        # Embed all results once after loading all data
        return solution_result.embedding_all_results()
    
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
                    solution_name=solution_name,
                    dataSet=dataSet,
                    repeat_id=repeat_id,
                    analysis_matrix=eval_matrix_label,
                    category=res.get_category(),
                    query=res.get_prompt(),
                    raw_answer=res.get_raw_response(),
                    product=res.get_product(),
                    result=float(score)
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
            solution_name = matrix[0]
            dataset = matrix[1]
            repeat_id = matrix[2]
            category = matrix[4]
            query = matrix[3]
            raw_answer = matrix[6]
            product = matrix[7]
            
            evaluation_result.add_result(
                solution_name=solution_name, 
                dataSet=dataset, 
                repeat_id=repeat_id, 
                analysis_matrix=analysis_matrix, 
                category=category, 
                query=query,
                raw_answer=raw_answer,
                product=product,
                result=float(score)
            )
        
        return evaluation_result


class EvaluationResult(List[Tuple[Tuple[str, str, str, str, str, str, Tuple[str, str]], float]]):
    """
    The structure of the evaluation result:
    Structure:
        [
            ((solution_name, dataSet, repeat_id, analysis_matrix, category, query, (raw_answer, product)), float),
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
        query: str,
        raw_answer: str,
        product: str,
        result: float
    ) -> None:
        """
        Add a new result to the EvaluationResult.
        If the key exists, its value must not be replaced.
        We must keep all the results.
        """
        key = (solution_name, dataSet, repeat_id, analysis_matrix, category, query, (raw_answer, product))
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
            self.add_result(
                solution_name=k[0],
                dataSet=k[1],
                repeat_id=k[2],
                analysis_matrix=k[3],
                category=k[4],
                query=k[5],
                raw_answer=k[6][0],
                product=k[6][1],
                result=v
            )
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
            "query": 5,
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
            "query": 5,
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
    
    def group_by_attrs(self, attrs: List[str]) -> Dict[Tuple[str, ...], "EvaluationResult"]:
        """
        Group the results by the specified attributes.
        """
        idx_map = {
            "solution_name": 0,
            "dataSet": 1,
            "repeat_id": 2,
            "analysis_matrix": 3,
            "category": 4,
            "query": 5,
        }
        
        # Get indices for the requested attributes
        indices = [idx_map[attr] for attr in attrs if attr in idx_map]
        
        grouped = {}
        for key, val in self:
            # Create tuple of values for the specified attributes
            group_key = tuple(key[i] for i in indices)
            
            if group_key not in grouped:
                grouped[group_key] = EvaluationResult()
            grouped[group_key].append((key, val))
        
        return grouped
    
    def save(self, file_path: str) -> None:
        """
        Save the EvaluationResult to a JSON file.
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, file_path: str) -> "EvaluationResult":
        """
        Load the EvaluationResult from a JSON file.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return cls(json.load(f))
    
    def fliter_only_has_product(self) -> "EvaluationResult":
      """
      Filter the EvaluationResult to only keep the results with product.
      for each batch, we only keep the query with all results have product.
      """
      result = EvaluationResult()
      # group by query and batch
      grouped = self.group_by_attrs(["query", "batch"])

      for query_results in grouped.values():
          # check if all results have product
          if all(result[0][6][1] != {'name': None, 'url': None, 'desc': None} for result in query_results):
              result.extend(query_results)
      return result

    
    def average_by_batch(self) -> "EvaluationResult":
        """
        Average the EvaluationResult by repeat_id (batch).
        Groups by solution_name, dataSet, analysis_matrix, category, query
        and averages across different repeat_id values.
        """
        result = EvaluationResult()
        
        # Group by all attributes except repeat_id to average across batches
        grouped = self.group_by_attrs(["solution_name", "dataSet", "analysis_matrix", "category", "query"])
        
        for group_key, group_results in grouped.items():
            if not group_results:
                continue
                
            # Calculate average score across all repeat_ids in this group
            scores = [score for _, score in group_results]
            avg_score = sum(scores) / len(scores)
            
            # Use the first result as template and update with averaged score
            first_result = group_results[0]
            template_key = first_result[0]
            
            # Create new key with "avg" as repeat_id
            avg_key = (
                template_key[0],  # solution_name
                template_key[1],  # dataSet  
                "avg",           # repeat_id (averaged)
                template_key[3],  # analysis_matrix
                template_key[4],  # category
                template_key[5],  # query
                template_key[6]   # (raw_answer, product)
            )
            
            result.append((avg_key, avg_score))
            
        return result
    
    def export_method_result_with_score_threshold(self, 
        up_threshold: float=100, 
        lower_threshold: float=0,
        solution_name: str=None, matrix: str=None) -> "EvaluationResult":
        """
        Export the method result with score_threshold.
        """
        result = EvaluationResult()
        # group by solution_name
        grouped = self.group_by_attr("solution_name")
        for sol_name, results in grouped.items():
            # export the results less than score_threshold
            if solution_name is not None and sol_name != solution_name:
                continue
            for res in results:
                # Check matrix filter (analysis_matrix is at index 3 in the key tuple)
                if matrix is not None and res[0][3] != matrix:
                    continue
                if res[1] <= up_threshold and res[1] >= lower_threshold:
                    result.append(res)
        return result
    
    def export_compare_result_same_query_with_different_threshold(
        self,
        method_name_1: str,
        method_name_2: str,
        up_threshold_1: float = 100,
        lower_threshold_1: float = 0,
        up_threshold_2: float = 100,
        lower_threshold_2: float = 0,
        filter_solution: str = None,                 # 重命名，避免与 export 方法内部参数冲突
        matrix: str = None,
    ) -> "EvaluationResult":
        """
        比较同一批 query 在 两个方法/阈值 组合下的得分；
        只保留两者都命中的 queries，并按 query 输出一对结果，方便对比。
        """
        result = EvaluationResult()

        # 1. 分别获取 两组结果
        res1 = self.export_method_result_with_score_threshold(
            up_threshold=up_threshold_1,
            lower_threshold=lower_threshold_1,
            solution_name=method_name_1,
            matrix=matrix,
        )
        res2 = self.export_method_result_with_score_threshold(
            up_threshold=up_threshold_2,
            lower_threshold=lower_threshold_2,
            solution_name=method_name_2,
            matrix=matrix,
        )

        # 2. 用 dict 映射 (ds, run, query) -> ((sol, mat, cat, raw, prod), score)
        map1 = {}
        for item in res1:
            key, score = item
            sol, ds, run, mat, cat, query, (raw_ans, prod) = key
            map1[(ds, run, query)] = ((sol, mat, cat, raw_ans, prod), score)
        
        map2 = {}
        for item in res2:
            key, score = item
            sol, ds, run, mat, cat, query, (raw_ans, prod) = key
            map2[(ds, run, query)] = ((sol, mat, cat, raw_ans, prod), score)

        # 3. 取交集
        common_keys = set(map1.keys()) & set(map2.keys())

        # 4. 遍历每个共同 query，依次把方法1和方法2的结果 append 进 EvaluationResult
        for ds, run, query in sorted(common_keys):
            (sol1, mat1, cat1, raw1, prod1), score1 = map1[(ds, run, query)]
            (sol2, mat2, cat2, raw2, prod2), score2 = map2[(ds, run, query)]

            # 额外的 solution 过滤 - 只保留至少一个方法匹配的结果
            if sol1 != filter_solution or sol2 != filter_solution:
                continue
            # 额外的 matrix 过滤
            if matrix and (mat1 != matrix or mat2 != matrix):
                continue

            result.append(((sol1, ds, run, mat1, cat1, query, (raw1, prod1)), score1))
            result.append(((sol2, ds, run, mat2, cat2, query, (raw2, prod2)), score2))

        return result
    
    def export_compare_result_same_query_with_larger_score(
        self,
        method_name_1: str,
        method_name_2: str,
        difference_threshold: float = 0.1,
        matrix: str = None,
    ) -> "EvaluationResult":
        """
        Export all (key,score) pairs where for the same
        (dataset,run,query,matrix) method_name_1 outscored
        method_name_2 by more than difference_threshold.
        """
        result = EvaluationResult()

        # 1. Filter and collect entries for each method
        entries1 = [
            (key, score) for key, score in self
            if key[0] == method_name_1 and (matrix is None or key[3] == matrix)
        ]
        entries2 = [
            (key, score) for key, score in self
            if key[0] == method_name_2 and (matrix is None or key[3] == matrix)
        ]

        # 2. Build lookup maps keyed by (ds, run, query, mat)
        map1 = {}
        for key, score in entries1:
            _, ds, run, mat, _, query, _ = key
            map1[(ds, run, query, mat)] = (key, score)

        map2 = {}
        for key, score in entries2:
            _, ds, run, mat, _, query, _ = key
            map2[(ds, run, query, mat)] = (key, score)

        # 3. Compare only the common keys
        for batch_q_mat in sorted(set(map1) & set(map2)):
            (k1, score1), (k2, score2) = map1[batch_q_mat], map2[batch_q_mat]
            if score1 - score2 > difference_threshold:
                result.append((k1, score1))
                result.append((k2, score2))

        return result

    def graph_show_score_difference_distribution(
        self,
        method_name_1: str,
        method_name_2: str,
        matrix: str = None,
        bins: int = None,
        export_json_path: str = None
    ):
        import matplotlib.pyplot as plt

        map1 = {}
        map2 = {}
        for (sol, ds, run, mat, _, query, _), score in self:
            if matrix and mat != matrix:
                continue
            key4 = (ds, run, query, mat)
            if sol == method_name_1:
                map1[key4] = score
            elif sol == method_name_2:
                map2[key4] = score

        common = set(map1) & set(map2)
        diffs = [map1[k] - map2[k] for k in sorted(common)]
        if not diffs:
            print("No matching entries to compare.")
            return

        # ------------------------------------------------------------
        # Optionally export distribution data as JSON
        # ------------------------------------------------------------
        if export_json_path:
            from collections import Counter
            import json
            diff_counter = Counter(diffs)
            distribution_dict = {f"{k:.4f}": v for k, v in sorted(diff_counter.items())}
            try:
                with open(export_json_path, "w", encoding="utf-8") as fp:
                    json.dump(distribution_dict, fp, ensure_ascii=False, indent=2)
                print(f"Distribution data exported to {export_json_path}")
            except Exception as exc:
                print(f"Failed to export distribution to {export_json_path}: {exc}")

        # Draw histogram and capture bin edges for precise tick labeling
        if bins:
            counts, bin_edges, _ = plt.hist(diffs, bins=bins, edgecolor='black')
        else:
            counts, bin_edges, _ = plt.hist(diffs, edgecolor='black') 

        # Use bin edges as x-axis ticks for accuracy
        tick_positions = bin_edges
        # If there are too many ticks, sample to avoid overcrowding
        max_ticks = 20
        if len(tick_positions) > max_ticks:
            step = max(1, len(tick_positions) // max_ticks)
            tick_positions = tick_positions[::step]
        plt.xticks(tick_positions, [f"{edge:.2f}" for edge in tick_positions], rotation=45)

        plt.xlabel(f"Score Difference ({method_name_1} − {method_name_2})")
        plt.ylabel("Frequency")
        title = f"Distribution of Score Differences"
        if matrix:
            title += f" for '{matrix}'"
        plt.title(title)

        plt.tight_layout()
        plt.show()

    def export_compare_result_same_query_with_larger_score_top_n(
        self,
        method_name_1: str,
        method_name_2: str,
        top_n: int = 10,
        matrix: str = None,
    ) -> "EvaluationResult":
        """
        Export the top-N query results where ``method_name_1`` outperforms ``method_name_2`` by
        the largest margin (``score1 − score2`` is positive).

        Parameters
        ----------
        method_name_1 : str
            The primary method whose scores will be compared (treated as baseline).
        method_name_2 : str
            The secondary method being compared against.
        top_n : int, default 10
            Number of queries with the largest positive score difference to export.
        matrix : str, optional
            If provided, restrict comparison to this analysis matrix.

        Returns
        -------
        EvaluationResult
            A new EvaluationResult that contains **both** method results for each of the
            selected queries (so length == 2 * top_n).  The pairs are appended in
            descending order of the difference value.
        """
        result = EvaluationResult()

        # 1. Gather entries for each method with optional matrix filter
        entries1 = [
            (key, score) for key, score in self
            if key[0] == method_name_1 and (matrix is None or key[3] == matrix)
        ]
        entries2 = [
            (key, score) for key, score in self
            if key[0] == method_name_2 and (matrix is None or key[3] == matrix)
        ]

        # 2. Build lookup maps keyed by (ds, run, query, mat)
        map1: Dict[Tuple[str, str, str, str], Tuple[Tuple, float]] = {}
        for key, score in entries1:
            _, ds, run, mat, _, query, _ = key
            map1[(ds, run, query, mat)] = (key, score)

        map2: Dict[Tuple[str, str, str, str], Tuple[Tuple, float]] = {}
        for key, score in entries2:
            _, ds, run, mat, _, query, _ = key
            map2[(ds, run, query, mat)] = (key, score)

        # 3. Calculate score differences for shared queries
        diff_records: List[Tuple[float, Tuple, float, Tuple, float]] = []  # (diff, key1, score1, key2, score2)
        for shared_key in set(map1) & set(map2):
            (k1, score1) = map1[shared_key]
            (k2, score2) = map2[shared_key]
            diff = score1 - score2  # positive if method1 > method2
            if diff > 0:  # only keep positive improvements
                diff_records.append((diff, k1, score1, k2, score2))

        # 4. Sort by diff descending and pick top_n
        diff_records.sort(key=lambda x: x[0], reverse=True)
        selected = diff_records[:top_n]

        # 5. Append the selected pairs into the resulting EvaluationResult
        for _diff, k1, s1, k2, s2 in selected:
            result.append((k1, s1))
            result.append((k2, s2))

        return result

    def graph_show_matrix_score_distribution(self, matrix: str):
        import numpy as np
        filtered_results = []
        for (sol, ds, run, mat, _, _q, (_r, _p)), score in self:
            if mat == matrix:
                filtered_results.append((sol, score))
        
        grouped = defaultdict(list)
        for sol, score in filtered_results:
            grouped[sol].append(score)
        
        all_scores = [score for scores in grouped.values() for score in scores]
        bins = np.linspace(min(all_scores), max(all_scores), 11)  # 10 个区间
        
        n_groups = len(grouped)
        bar_width = (bins[1] - bins[0]) / (n_groups + 1)
        colors = plt.cm.Set1(np.linspace(0, 1, n_groups))
        
        for i, (sol_name, scores) in enumerate(grouped.items()):
            counts, _ = np.histogram(scores, bins=bins)
            positions = bins[:-1] + i * bar_width
            plt.bar(
                positions,
                counts,
                width=bar_width,
                align='edge',
                label=sol_name,
                alpha=0.8,
                color=colors[i]
            )
        
        plt.xlabel('Score')
        plt.ylabel('Frequency')
        plt.title(f'Score Distribution for {matrix}')
        plt.xticks(bins, rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.show()


    def to_dict_report(self, output_dir: Optional[str]=None) -> Dict[str, Any]:
        """
        Convert flat list into nested dictionary report with averages (__all__ entries).
        """
        report: Dict[str, Any] = {}

        # Build bottom-level nesting
        for (sol, ds, run, mat, _, _q,(_r,_p)), score in self:
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
            dir_path = os.path.dirname(output_dir)
            if dir_path:  # Only create directory if there is a directory path
                os.makedirs(dir_path, exist_ok=True)
            report_path = os.path.join(dir_path, "report.json") if dir_path else "report.json"
            with open(report_path, "w") as f:
                json.dump(report, f, indent=4)

        return report

    def save_to_excel_report(self, file_path: str, title: str="Report") -> "EvaluationResult":
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
            return self
        
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
            color_scheme=color_scheme,
            title=title
        )
        report.create_report_excel()
        return self
