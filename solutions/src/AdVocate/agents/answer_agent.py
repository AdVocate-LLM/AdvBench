from .base_agent import BaseAgent
from ..utils.oracle import Oracle
from ..utils.result import Result
from typing import List
from ..prompt.answer_prompt import RAW_ANSWER


class AnswerAgent(BaseAgent):
    def __init__(self, model:str):
        super().__init__(model)
        self.system_prompt = RAW_ANSWER
        
    def raw_answer(self, problem_list: List[str]) -> List[Result]:
        answers = self.answer_multiple(problem_list)
        results = []
        _idx=1
        for a in answers:
            if a and a["answer"] != "QUERY_FAILED":
                results.append(Result(prompt=a["query"], answer=a["answer"]))
            else:
                self.error(f"Query failed for problem(with index {_idx}): {a['query']}")
            _idx += 1
        self.debug(f"The number of results is: {len(results)}, the number of failed results is: {len([result for result in results if result.get_answer() == 'QUERY_FAILED'])}")
        return results