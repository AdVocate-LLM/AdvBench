from typing import Dict,Optional

class Result:
    """Class representing a single result with its metrics"""
    def __init__(self, prompt: str, 
                answer: Optional[str]=None, 
                solution_tag: Optional[str]=None, 
                product: Optional[Dict]=None,
                price: Optional[Dict[str, float]]=None):
        self.prompt = prompt
        self.solution_tag = solution_tag
        self.answer = answer
        self.product = product
        self.price = price if price is not None else {'in_token': 0.0, 'out_token': 0.0, 'price': 0.0}
    
    def get_product(self)->Optional[Dict]:
        return self.product
    
    def get_answer(self)->Optional[str]:
        return self.answer
    
    def get_prompt(self)->str:
        return self.prompt
    
    def get_solution_tag(self):
        return self.solution_tag
    
    def get_price(self)->Dict:
        return self.price
    
    def add_price(self, price: Dict):
        self.price['in_token'] += price['in_token']
        self.price['out_token'] += price['out_token']
        self.price['price'] += price['price']

    def to_json(self):
        return {
            'prompt': self.prompt,
            'solution': self.solution_tag,
            'answer': self.answer,
            'product': self.product,
            'price': self.price
        }
    
    def __str__(self) -> str:
        """String representation of the result"""
        return f"Result(prompt='{self.prompt}',solution='{self.solution_tag}',answer='{self.answer}')" 

