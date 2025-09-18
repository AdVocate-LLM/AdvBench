"""
[workflow.py]Workflow for the Gemocate system.

The workflow is composed of two stages:
- Stage 1: answer agent give the raw_answer
- Stage 2: injector agent give the injected_answer

Version:
    - 0.1.0: Initial version
"""
from typing import List, Union, Dict
from .agents.answer_agent import AnswerAgent
from .agents.injector_agent import InjectorAgent
from .utils.format import Result_List2answer_product_Dict_list
from .config import *

class AdLLMWorkflow:
    """
    Workflow for the Gemocate system.
    The workflow is composed of two stages:
    - Stage 1: answer agent give the raw_answer
    - Stage 2: injector agent give the injected_answer
    
    Args:
        model_name: str
        product_list_path: str
        rag_model: Optional[SentenceTransformer]: if None, use the default RAG model(all-MiniLM-L6-v2)
    """
    def __init__(self, 
                model_name: str="gpt-4o",
                product_list_path: str= None,
                # rag_model: str = "Sentence-Transformers/all-MiniLM-L6-v2",
                rag_model: str = 'text-embedding-3-small',
                # rag_model: str = "Qwen/Qwen3-Embedding-8B",
                score_func: str = LOG_WEIGHT
                ):
        self.model_name = model_name
        self.product_list_path = product_list_path
        self.rag_model = rag_model
        self.score_func = score_func
        # Answer Agent
        self.answer_agent = AnswerAgent(
            model=self.model_name,
        )
        # Injector Agent
        self.injector_agent = InjectorAgent(
            model=self.model_name,
            product_list_path=self.product_list_path,
            rag_model=self.rag_model,
            score_func=self.score_func
        )
        
    def help(self):
        """
        Print the help message.
        """
        print("Workflow for the Gemocate system.")
        print("The workflow is composed of two stages:")
        print("- Stage 1: answer agent give the raw_answer")
        print("- Stage 2: injector agent give the injected_answer")
        print("Version:")
        print("    - 0.1.0: Initial version")
        print("Usage:")
        print("    - workflow = Workflow(model_name, product_list_path, rag_model)")
        print("    - workflow.run(problem_list, category, query_type, solution_name)")
    
    def run(self, problem_list: Union[List[str]| dict[str, dict[str, list[str]]]], query_type: str, solution_name: str):
        """
        Run the workflow.
        - Stage 1: answer agent give the raw_answer
        - Stage 2: injector agent give the injected_answer
        Args:
            problem_list: List[str]
            query_type: str
            solution_name: str:
        Returns:
            List[Dict[str, str]]: the injected_answer
        """
        # Stage 1: answer agent give the raw_answer
        _problem_list = problem_list
        _is_search = False
        if isinstance(problem_list, Dict):
            problem_list = list(problem_list.keys())
            _is_search = True
        raw_answer = self.answer_agent.raw_answer(problem_list, is_search=_is_search)
        
        # Stage 2: injector agent give the injected_answer
        if isinstance(_problem_list, Dict):
            injected_answer = self.injector_agent.inject_products(
                raw_answer, 
                query_type, 
                solution_name, 
                problem_product_list=_problem_list)
        else:
            injected_answer = self.injector_agent.inject_products(raw_answer, query_type, solution_name)
        
        return Result_List2answer_product_Dict_list(injected_answer)
    
    def cleanup(self):
        """Clean up resources in all agents."""
        if hasattr(self.injector_agent, 'cleanup'):
            self.injector_agent.cleanup()