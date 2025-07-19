from typing import List, Dict

class Result:
    """Class representing a single result with its metrics"""
    def __init__(self, prompt: str, 
                answer: str=None, 
                solution_tag: str=None, 
                product: List[Dict]=None):
        self.prompt = prompt
        self.solution_tag = solution_tag
        self.answer = answer
        self.product = product
    
    def get_product(self):
        return self.product
    
    def get_answer(self):
        return self.answer
    
    def get_prompt(self):
        return self.prompt
    
    def get_solution_tag(self):
        return self.solution_tag

    def to_json(self):
        return {
            'prompt': self.prompt,
            'solution': self.solution_tag,
            'answer': self.answer,
            'product': self.product
        }
    
    def __str__(self) -> str:
        """String representation of the result"""
        return f"Result(prompt='{self.prompt}',solution='{self.solution_tag}',answer='{self.answer}')" 

