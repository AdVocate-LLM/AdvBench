"""
[workflow.py]Workflow for the Advocate system.

The workflow is composed of two stages:
- Stage 1: answer agent give the raw_answer
- Stage 2: injector agent give the injected_answer

Version:
    - 0.1.0: Initial version
"""
from typing import List, Optional, Dict
from sentence_transformers import SentenceTransformer
from .agents.answer_agent import AnswerAgent
from .agents.injector_agent import InjectorAgent
from .utils.format import Result_List2answer_product_Dict_list

class AdvocateWorkflow:
    """
    Workflow for the Advocate system.
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
                rag_model: Optional[SentenceTransformer] = None,
                ):
        self.model_name = model_name
        self.product_list_path = product_list_path
        self.rag_model = rag_model
        # Answer Agent
        self.answer_agent = AnswerAgent(
            model=self.model_name,
        )
        # Injector Agent
        self.injector_agent = InjectorAgent(
            model=self.model_name,
            product_list_path=self.product_list_path,
            rag_model=self.rag_model,
        )
        
    def help(self):
        """
        Print the help message.
        """
        print("Workflow for the Advocate system.")
        print("The workflow is composed of two stages:")
        print("- Stage 1: answer agent give the raw_answer")
        print("- Stage 2: injector agent give the injected_answer")
        print("Version:")
        print("    - 0.1.0: Initial version")
        print("Usage:")
        print("    - workflow = Workflow(model_name, product_list_path, rag_model)")
        print("    - workflow.run(problem_list, category, query_type, solution_name)")
    
    def run(self, problem_list: List[str], query_type: str, solution_name: str):
        """
        Run the workflow.
        - Stage 1: answer agent give the raw_answer
        - Stage 2: injector agent give the injected_answer
        Args:
            problem_list: List[str]
            query_type: str
            solution_name: str:
        Returns:
            List[str]
        """
        # Stage 1: answer agent give the raw_answer
        raw_answer = self.answer_agent.raw_answer(problem_list)
        # Stage 2: injector agent give the injected_answer
        injected_answer = self.injector_agent.inject_products(raw_answer, query_type, solution_name)
        
        return Result_List2answer_product_Dict_list(injected_answer)
    
    def get_best_product(self, 
                            problem_product_list: dict[str, dict[str, list[str]]], 
                            query_type: str = "QUERY_RESPONSE")->Dict[str, Dict[str, str]]:
        """
        Get the best product for the problem.

        Args:
            solution_name: Name of the solution to use (BASIC_GEN_INSERT, REFINE_GEN_INSERT)
            problem_product_list: Dict of problem and product list
            query_type: Type of query to use (QUERY_PROMPT, QUERY_RESPONSE, QUERY_PROMPT_N_RESPONSE)

        Returns:
            Dict[str, Product]: the suitable products for the query
        """
        # Stage 1: answer agent give the raw_answer
        raw_answer = self.answer_agent.raw_answer(list(problem_product_list.keys()))
        # Stage 2: injector agent give the injected_answer
        best_product = self.injector_agent.get_suitable_product(
            raw_answers=raw_answer, 
            problem_product_list=problem_product_list,
            query_type=query_type
        )

        return best_product