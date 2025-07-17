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
        results = [Result(prompt=response["prompt"], answer=response["answer"]) for response in responses]
        self.debug(f"The number of results is: {len(results)}, the number of failed results is: {len([result for result in results if result.get_answer() == 'QUERY_FAILED'])}")
        return results