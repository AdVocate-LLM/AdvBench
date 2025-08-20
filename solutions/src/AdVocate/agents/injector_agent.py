from ..utils.result import Result
from ..utils.sentence import Sentence
from ..utils.product import Product
from ..utils.functions import get_adjacent_sentence_similarities
from ..utils.format import answer_structure2string
from typing import List, Tuple, Optional, Dict, Union
from ..prompt.injector_prompts import SYS_REFINE, USER_REFINE
from .base_agent import BaseAgent
# import tools for injector agent
from ..tools.productRAG import productRAG
from ..tools.injector import Injector
from ..utils.embedding import Embedding
from ..utils.functions import SentenceEmbedding
from ..config import *
import numpy as np

class InjectorAgent(BaseAgent):
    
    def __init__(self, 
                model: str, 
                product_list_path: str,
                rag_model: str,
                score_func: str = LOG_WEIGHT
                ) -> None:
        super().__init__(model)
        # basic settings
        self.product_list_path = product_list_path
        self.rag_model = Embedding(model_name=rag_model)
        self.system_prompt = SYS_REFINE
        self.score_func = score_func
        self.INJECT_METHODS = {
            "QUERY_PROMPT": QUERY_PROMPT, 
            "QUERY_RESPONSE": QUERY_RESPONSE, 
            "QUERY_PROMPT_N_RESPONSE": QUERY_PROMPT_N_RESPONSE
        }
        
        self.REFINE_METHODS = {
            "REFINE": REFINE_GEN_INSERT,
            "BASIC": BASIC_GEN_INSERT
        }
        self.injector = Injector(score_func=self.score_func)

    def get_inject_methods(self) -> Dict[str, str]:
        """Get available injection methods.
        
        Returns:
            Dict[str, str]: Dictionary of injection methods
        """
        return self.INJECT_METHODS

    def refine_content(self, content: str) -> Dict:
        """Refine the given content using the language model.
        
        Args:
            content (str): The content to be refined
            
        Returns:
            str: Refined text
        """
        usr_refine_ass = USER_REFINE.format(ori_text=content)
        response = self.answer(usr_refine_ass)
        return response

    def create_refined_injection(self, 
                            raw_answer: Result,
                            sol_tag: str,
                            sentences: List[Sentence], 
                            structure: List[Union[str, int]],
                            inject_position: Tuple[int, int], 
                            best_product: Product) -> Result:
        """Create a refined injection by inserting and optimizing the product.
        
        Args:
            raw_answer (Result): Original answer
            sentences (List[Sentence]): List of sentences
            structure (List[Union[str, int]]): Structure of the answer
            inject_position (Tuple[int, int]): Position to inject the product
            best_product (Product): Product to inject
            
        Returns:
            Result: Refined result with injected product
        """
        product_text = f"{ADS_START}{str(best_product)}{ADS_END}"
        target_idx = inject_position[0]
        
        # Handle single sentence case: if target_idx is out of bounds, append to the last sentence
        if target_idx >= len(sentences):
            target_idx = len(sentences) - 1
            target_sentence = sentences[target_idx].to_string()
            sentences[target_idx].sentence = f"{target_sentence} {product_text}"
        else:
            target_sentence = sentences[target_idx].to_string()
            sentences[target_idx].sentence = f"{target_sentence} {product_text}"
        content = answer_structure2string(sentences, structure)
        
        refined_text = content
        product={
            "name": None,
            "category": None,
            "desc": None,
            "url": None
        }
        refined = self.refine_content(content)
        if refined["answer"] != "QUERY_FAILED":
            refined_text = refined["answer"]
            product = best_product.show()
        refined_result = Result(
            prompt=raw_answer.get_prompt(),
            solution_tag=sol_tag,
            answer=refined_text,
            product=product
        )

        return refined_result
    
    def create_basic_injection(self, 
                            raw_answer: Result, 
                            sol_tag: str,
                            sentences: List[Sentence], 
                            structure: List[Union[str, int]], 
                            inject_position: Tuple[int, int], 
                            best_product: Product) -> Result:
        """Create a basic injection by inserting the product without optimization.
        
        Args:
            raw_answer (Result): Original answer
            sentences (List[Sentence]): List of sentences
            structure (List[Union[str, int]]): Structure of the answer
            inject_position (Tuple[int, int]): Position to inject the product
            best_product (Product): Product to inject
            
        Returns:
            Result: Result with injected product
        """
        product_text = str(best_product)
        target_idx = inject_position[0]
        
        # Handle single sentence case: if target_idx is out of bounds, append to the last sentence
        if target_idx >= len(sentences):
            target_idx = len(sentences) - 1
            target_sentence = sentences[target_idx].to_string()
            sentences[target_idx].sentence = f"{target_sentence} {product_text}"
        else:
            target_sentence = sentences[target_idx].to_string()
            sentences[target_idx].sentence = f"{target_sentence} {product_text}"
        content = answer_structure2string(sentences, structure)
        injected_result = Result(
            prompt=raw_answer.get_prompt(),
            solution_tag=sol_tag,
            answer=content,
            product=best_product.show()
        )
        return injected_result
    
    def get_query_text(self, raw_answer: Result, query_type: str) -> Optional[str]:
        """Extract query text based on query type.
        
        Args:
            raw_answer (Result): Original answer
            query_type (str): Type of query to extract
            
        Returns:
            str: Extracted query text
            
        Raises:
            ValueError: If query_type is invalid
        """
        if query_type == self.INJECT_METHODS["QUERY_PROMPT"]:
            return raw_answer.get_prompt()
        elif query_type == self.INJECT_METHODS["QUERY_RESPONSE"]:
            return raw_answer.get_answer()
        elif query_type == self.INJECT_METHODS["QUERY_PROMPT_N_RESPONSE"]:
            return raw_answer.get_prompt() + raw_answer.get_answer()
        raise ValueError(f"Invalid query_type: {query_type}")
    
    def inject_products_single(self, raw_answer, query_type, solution_name):
        """Process a single answer to inject a product.
        
        Args:
            raw_answer (Result): Raw answer to process
            query_type (str): Type of query to use
            solution_name (str): Name of the solution to use
            
        Returns:
            Result: Result with injected product
        """
        # Step 0: Get the question based on the method
        query = self.get_query_text(raw_answer, query_type)
        # Step 1: Get the best product
        product_rag = productRAG(
            file_path=self.product_list_path,
            model=self.rag_model
        )
        products = product_rag.query(query, top_k=5)
        # convert the sentences to sentences
        sentences, structure = SentenceEmbedding(raw_answer.get_answer(), self.rag_model).embed()[0]
        sentence_flow = get_adjacent_sentence_similarities(sentences)
        best_product, prev_pos, next_pos, disrupt = self.injector.get_best_inject_product(
            sentences, sentence_flow, products
        )
        # Step 2: Inject the best product based on the solution
        sol_tag = f'{solution_name}_{query_type}'
        # only inject the product without optimization
        if solution_name == BASIC_GEN_INSERT:
            return self.create_basic_injection(
                raw_answer, sol_tag, sentences, structure, (prev_pos, next_pos), best_product
            )
        # inject the product and optimize the content
        elif solution_name == REFINE_GEN_INSERT:
            return self.create_refined_injection(
                raw_answer, sol_tag, sentences, structure, (prev_pos, next_pos), best_product
            )
    
    def inject_products(self, 
                    raw_answers: List[Result],
                    query_type: str = QUERY_RESPONSE,
                    solution_name: str = REFINE_GEN_INSERT,
                    ) -> List[Result]:
        """Inject products into the answers at optimal positions with optimized parallel processing.
        
        Args:
            raw_answers (List[Result]): List of raw answers
            query_type (str): Type of query to use | QUERY_PROMPT, QUERY_RESPONSE, QUERY_PROMPT_N_RESPONSE
            solution_name (str): Name of the solution to use | BASIC_GEN_INSERT, REFINE_GEN_INSERT
            
        Returns:
            List[Result]: List of results with injected products
        """
        
        suitable_products = []
        # Step 0: preprocess the answer
        # base on query_type, get the query
        query_texts = [self.get_query_text(raw_answer, query_type) for raw_answer in raw_answers]
        sentence_embedding = SentenceEmbedding(query_texts, self.rag_model)
        embedding_list = sentence_embedding.embed()
        embedded_queries = self.rag_model.encode_all(text_list=query_texts)
        embedded_queries_st = [embedding[0] for embedding in embedding_list]
        embedded_st_structures = [embedding[1] for embedding in embedding_list]
        # Step 1: get the suitable products for the query
        product_rag = productRAG(
            file_path=self.product_list_path,
            model=self.rag_model
        )
        for embedded_query, embedded_query_st in zip(embedded_queries, embedded_queries_st):
            products = product_rag.query(np.array(embedded_query[1]), top_k=5)
            sentence_flow = get_adjacent_sentence_similarities(embedded_query_st)
            best_product, prev_pos, next_pos, disrupt = self.injector.get_best_inject_product(
                embedded_query_st, sentence_flow, products
            )
            suitable_products.append(best_product)
        # Step 2: Inject the best product based on the solution
        sol_tag = f'{solution_name}_{query_type}'
        injected_results: List[Result] = []
        for raw_answer, best_product, embedded_query_st, embedded_structure in zip(raw_answers, suitable_products, embedded_queries_st, embedded_st_structures):            # only inject the product without optimization
            if solution_name == BASIC_GEN_INSERT:
                injected_results.append(self.create_basic_injection(
                    raw_answer, sol_tag, embedded_query_st, embedded_structure, (prev_pos, next_pos), best_product
                ))
            # inject the product and optimize the content
            elif solution_name == REFINE_GEN_INSERT:
                injected_results.append(self.create_refined_injection(
                    raw_answer, sol_tag, embedded_query_st, embedded_structure, (prev_pos, next_pos), best_product
                ))
        return injected_results

    def get_suitable_product(self, raw_answers: List[Result], problem_product_list: Dict[str, List[Dict]], query_type: str = "QUERY_RESPONSE"):
        """
        Get the suitable products for the problem.

        Args:
            raw_answers (List[Result]): List of raw answer results
            solution_name (str): Name of the solution to use (BASIC_GEN_INSERT, REFINE_GEN_INSERT)
            problem_product_list (Dict[str, List[Dict]]): Dict of problem and product list
            query_type (str): Type of query to use (QUERY_PROMPT, QUERY_RESPONSE, QUERY_PROMPT_N_RESPONSE)

        note: the problem_product_list would be like this:
        {
            "query1": [
                {"name": "product1", "desc": "product1 description", "category": "cluster1", "url": "url1", embedding: np.array[0.1, 0.2, ...]},
                {"name": "product2", "desc": "product2 description", "category": "cluster2", "url": "url2", embedding: np.array[0.1, 0.2, ...]}
            ],
            "query2": [
                {"name": "product3", "desc": "product3 description", "category": "cluster3", "url": "url3", embedding: np.array[0.1, 0.2, ...]},
                {"name": "product4", "desc": "product4 description", "category": "cluster4", "url": "url4", embedding: np.array[0.1, 0.2, ...]}
            ],
            ...
        }

        Returns:
            Dict[str, Dict[str, str]]: Dict of query and suitable products for the query
        """
        suitable_products = {}
        # Step 0: preprocess the answer
        # base on query_type, get the query
        queries = [raw_answer.get_prompt() for raw_answer in raw_answers]
        query_texts = [self.get_query_text(raw_answer, query_type) for raw_answer in raw_answers]
        sentence_embedding = SentenceEmbedding(query_texts, self.rag_model)
        embedding_list = sentence_embedding.embed()
        embedded_queries = self.rag_model.encode_all(text_list=query_texts)
        embedded_queries_st = [embedding[0] for embedding in embedding_list]
        for query, embedded_query, embedded_query_st in zip(queries, embedded_queries, embedded_queries_st):
            product_rag = productRAG(
                file_path=None,
                product_list=problem_product_list.get(query, []),
                model=self.rag_model
            )
            products = product_rag.query(np.array(embedded_query[1]), top_k=5)
            sentence_flow = get_adjacent_sentence_similarities(embedded_query_st)
            best_product, prev_pos, next_pos, disrupt = self.injector.get_best_inject_product(
                embedded_query_st, sentence_flow, products
            )
            suitable_products[query] = best_product.to_dict()
    
        return suitable_products