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
        responses = self.answer_multiple(problem_list)
        results = []
        for i, (q,a) in enumerate(zip(problem_list, responses)):
            if a and a != "QUERY_FAILED":
                results.append(Result(prompt=q, answer=a))
            else:
                self.error(f"Query failed for problem(with index {i}): {q}")
        self.debug(f"The number of results is: {len(results)}, the number of failed results is: {len([result for result in results if result.get_answer() == 'QUERY_FAILED'])}")
        return results