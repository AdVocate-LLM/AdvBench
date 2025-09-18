from .base_agent import BaseAgent
from ..utils.result import Result
from typing import List
from ..prompt.answer_prompt import RAW_ANSWER, SEARCH_ANSWER


class AnswerAgent(BaseAgent):
    def __init__(self, model:str):
        super().__init__(model)
        self.system_prompt = RAW_ANSWER
        
    def raw_answer(self, problem_list: List[str], is_search=False) -> List[Result]:
        if is_search:
            self.system_prompt = SEARCH_ANSWER
        else:
            self.system_prompt = RAW_ANSWER
        answers = self.answer_multiple(problem_list)
        results = []
        _idx=1
        for a in answers:
            if a and "QUERY_FAILED:" not in a["answer"]:
                results.append(Result(prompt=a["query"], answer=a["answer"], price=a["price"]))
            else:
                self.error(f"Query failed for problem(with index {_idx}): {a['query']}, error: {a['answer']}")
            _idx += 1
        self.debug(f"The number of results is: {len(results)}, the number of failed results is: {len([result for result in results if 'QUERY_FAILED:' in result.get_answer()])}")
        return results