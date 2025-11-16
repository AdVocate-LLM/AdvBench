from ..utils.result import Result
from ..utils.sentence import Sentence
from ..utils.product import Product
from ..utils.functions import get_adjacent_sentence_similarities
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
                score_func: str = LOG_WEIGHT,
                k: int = 1
                ) -> None:
        super().__init__(model)
        # basic settings
        self.product_list_path = product_list_path
        self.rag_model = Embedding(model_name=rag_model)
        self.system_prompt = SYS_REFINE
        self.score_func = score_func
        self.k = k  # Number of products to inject per query
        # Cache for product RAG instances to avoid repeated initialization
        self._product_rag_cache = None
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

    def _get_product_rag(self) -> 'productRAG':
        """Get or create cached productRAG instance."""
        if self._product_rag_cache is None:
            self._product_rag_cache = productRAG(
                file_path=self.product_list_path,
                model=self.rag_model
            )
        return self._product_rag_cache

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
            Dict: Refined response
        """
        usr_refine_ass = USER_REFINE.format(ori_text=content)
        response = self.answer(usr_refine_ass)
        return response
    
    def refine_contents_batch(self, contents: List[str]) -> List[Dict]:
        """Batch refine multiple contents using the language model for better performance.
        
        Args:
            contents (List[str]): List of contents to be refined
            
        Returns:
            List[Dict]: List of refined responses
        """
        user_prompts = [USER_REFINE.format(ori_text=content) for content in contents]
        responses = self.answer_multiple(user_prompts)
        return responses

    def create_refined_injection(self,
                            raw_answer: Result,
                            sol_tag: str,
                            sentences: List[Sentence],
                            structure: List[Union[str, int]],
                            inject_positions: List[Tuple[int, int]],
                            best_products: List[Product]) -> Result:
        """Create a refined injection by inserting and optimizing the products.

        Args:
            raw_answer (Result): Original answer
            sentences (List[Sentence]): List of sentences
            structure (List[Union[str, int]]): Structure of the answer (not used, kept for compatibility)
            inject_positions (List[Tuple[int, int]]): Positions to inject the products between sentences
            best_products (List[Product]): Products to inject

        Returns:
            Result: Refined result with injected products
        """
        # Sort products by position (descending) to insert from end to start
        sorted_injections = sorted(
            zip(inject_positions, best_products),
            key=lambda x: x[0][0],
            reverse=True
        )

        # Build content by concatenating sentences with product injections
        content_parts = []
        for i, sentence in enumerate(sentences):
            content_parts.append(sentence.to_string())
            # Check if any products should be inserted after this sentence
            for (prev_pos, next_pos), product in sorted_injections:
                if i == prev_pos:
                    content_parts.append(" ")  # Add space before product
                    content_parts.append(f"{ADS_START}{str(product)}{ADS_END}")
                    content_parts.append(" ")  # Add space after product

        content = "".join(content_parts)

        refined_text = content
        products_info = [
            {"name": None, "category": None, "desc": None, "url": None}
            for _ in best_products
        ]

        refined = self.refine_content(content)
        if refined["answer"] != "QUERY_FAILED":
            refined_text = refined["answer"]
            products_info = [product.show() for product in best_products]

        refined_result = Result(
            prompt=raw_answer.get_prompt(),
            solution_tag=sol_tag,
            answer=refined_text,
            product=products_info if len(products_info) > 1 else products_info[0] if products_info else {"name": None, "category": None, "desc": None, "url": None},
            price=refined["price"]
        )

        return refined_result
    
    def create_basic_injection(self,
                            raw_answer: Result,
                            sol_tag: str,
                            sentences: List[Sentence],
                            structure: List[Union[str, int]],
                            inject_positions: List[Tuple[int, int]],
                            best_products: List[Product]) -> Result:
        """Create a basic injection by inserting the products without optimization.

        Args:
            raw_answer (Result): Original answer
            sentences (List[Sentence]): List of sentences
            structure (List[Union[str, int]]): Structure of the answer (not used, kept for compatibility)
            inject_positions (List[Tuple[int, int]]): Positions to inject the products between sentences (sentence indices)
            best_products (List[Product]): Products to inject

        Returns:
            Result: Result with injected products
        """
        # Sort products by position (descending) to insert from end to start
        sorted_injections = sorted(
            zip(inject_positions, best_products),
            key=lambda x: x[0][0],
            reverse=True
        )

        # Build content by concatenating sentences with product injections
        content_parts = []
        for i, sentence in enumerate(sentences):
            content_parts.append(sentence.to_string())
            # Check if any products should be inserted after this sentence
            for (prev_pos, next_pos), product in sorted_injections:
                if i == prev_pos:
                    content_parts.append(" ")  # Add space before product
                    content_parts.append(product.ad_content())
                    content_parts.append(" ")  # Add space after product

        content = "".join(content_parts)

        # Collect all product information
        products_info = [product.show() for product in best_products]

        injected_result = Result(
            prompt=raw_answer.get_prompt(),
            solution_tag=sol_tag,
            answer=content,
            product=products_info if len(products_info) > 1 else products_info[0] if products_info else {"name": None, "category": None, "desc": None, "url": None},
            price=raw_answer.get_price()
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
        """Process a single answer to inject products (supports k products).

        Args:
            raw_answer (Result): Raw answer to process
            query_type (str): Type of query to use
            solution_name (str): Name of the solution to use

        Returns:
            Result: Result with injected products
        """
        # Step 0: Get the question based on the method
        query = self.get_query_text(raw_answer, query_type)
        # Step 1: Get the best products
        product_rag = self._get_product_rag()
        products = product_rag.query(query, top_k=max(5, self.k * 5))
        # convert the sentences to sentences
        sentences, structure = SentenceEmbedding(raw_answer.get_answer(), self.rag_model).embed()[0]
        sentence_flow = get_adjacent_sentence_similarities(sentences)

        # Get k best products and their positions
        best_products_with_positions = self.injector.get_best_inject_products(
            sentences, sentence_flow, products, k=self.k
        )

        # Separate products and positions
        best_products = [item[0] for item in best_products_with_positions]
        inject_positions = [(item[1], item[2]) for item in best_products_with_positions]

        # Step 2: Inject the best products based on the solution
        sol_tag = f'{solution_name}_{query_type}'
        # only inject the products without optimization
        if solution_name == BASIC_GEN_INSERT:
            return self.create_basic_injection(
                raw_answer, sol_tag, sentences, structure, inject_positions, best_products
            )
        # inject the products and optimize the content
        elif solution_name == REFINE_GEN_INSERT:
            return self.create_refined_injection(
                raw_answer, sol_tag, sentences, structure, inject_positions, best_products
            )
    
    def inject_products(self,
                    raw_answers: List[Result],
                    query_type: str = QUERY_RESPONSE,
                    solution_name: str = REFINE_GEN_INSERT,
                    problem_product_list: Optional[Dict[str, List[Dict]]]=None
                    ) -> List[Result]:
        """Inject products into the answers at optimal positions with optimized parallel processing.

        Args:
            raw_answers (List[Result]): List of raw answers
            query_type (str): Type of query to use | QUERY_PROMPT, QUERY_RESPONSE, QUERY_PROMPT_N_RESPONSE
            solution_name (str): Name of the solution to use | BASIC_GEN_INSERT, REFINE_GEN_INSERT

        Returns:
            List[Result]: List of results with injected products (k products per answer)
        """

        suitable_products = []
        inject_positions = []
        # Step 0: preprocess the answer
        query_texts = [self.get_query_text(raw_answer, query_type) for raw_answer in raw_answers]
        answer_texts = [raw_answer.get_answer() for raw_answer in raw_answers]
        sentence_embedding = SentenceEmbedding(answer_texts, self.rag_model)
        embedding_list = sentence_embedding.embed()
        embedded_queries = self.rag_model.encode_all(text_list=query_texts)
        embedded_queries_st = [embedding[0] for embedding in embedding_list]
        embedded_st_structures = [embedding[1] for embedding in embedding_list]
        # Step 1: get the suitable products for the query
        if problem_product_list is None:
            product_rag = self._get_product_rag()
        for embedded_query, embedded_query_st, raw_answer in zip(embedded_queries, embedded_queries_st, raw_answers):
            if problem_product_list is not None:
                # Use a specialized product RAG for this query's product list
                product_rag = productRAG(
                    file_path=None,
                    product_list=problem_product_list.get(raw_answer.get_prompt(), []),
                    model=self.rag_model
                )
            # Get more products to select from (at least 5 * k)
            products = product_rag.query(np.array(embedded_query[1]), top_k=max(5, self.k * 5))
            sentence_flow = get_adjacent_sentence_similarities(embedded_query_st)

            # Get k best products and their positions
            best_products_with_positions = self.injector.get_best_inject_products(
                embedded_query_st, sentence_flow, products, k=self.k
            )

            # Separate products and positions
            products_for_answer = [item[0] for item in best_products_with_positions]
            positions_for_answer = [(item[1], item[2]) for item in best_products_with_positions]

            suitable_products.append(products_for_answer)
            inject_positions.append(positions_for_answer)
        # Step 2: Inject the best products based on the solution
        sol_tag = f'{solution_name}_{query_type}'
        injected_results: List[Result] = []

        if solution_name == BASIC_GEN_INSERT:
            # Basic injection without refinement
            for raw_answer, best_products, embedded_query_st, embedded_structure, inject_positions_list in zip(raw_answers, suitable_products, embedded_queries_st, embedded_st_structures, inject_positions):
                injected_results.append(self.create_basic_injection(
                    raw_answer, sol_tag, embedded_query_st, embedded_structure, inject_positions_list, best_products
                ))
        elif solution_name == REFINE_GEN_INSERT:
            # Batch process refined injections for better performance
            # First, create all injected contents
            injected_contents = []
            for raw_answer, best_products, embedded_query_st, inject_positions_list in zip(raw_answers, suitable_products, embedded_queries_st, inject_positions):
                # Sort products by position (descending) to insert from end to start
                sorted_injections = sorted(
                    zip(inject_positions_list, best_products),
                    key=lambda x: x[0][0],
                    reverse=True
                )

                # Build content by concatenating sentences with product injections
                content_parts = []
                for i, sentence in enumerate(embedded_query_st):
                    content_parts.append(sentence.to_string())
                    # Check if any products should be inserted after this sentence
                    for (prev_pos, next_pos), product in sorted_injections:
                        if i == prev_pos:
                            content_parts.append(" ")
                            content_parts.append(f"{ADS_START}{str(product.ad_content())}{ADS_END}")
                            content_parts.append(" ")

                content = "".join(content_parts)
                injected_contents.append(content)

            # Batch refine all contents at once
            refined_responses = self.refine_contents_batch(injected_contents)

            # Create Result objects with refined content
            for idx, (raw_answer, best_products, refined) in enumerate(zip(raw_answers, suitable_products, refined_responses)):
                refined_text = injected_contents[idx]  # Default to non-refined
                products_info = [
                    {"name": None, "category": None, "desc": None, "url": None}
                    for _ in best_products
                ]

                if refined.get("answer") != "QUERY_FAILED":
                    refined_text = refined["answer"]
                    products_info = [product.show() for product in best_products]

                injected_results.append(Result(
                    prompt=raw_answer.get_prompt(),
                    solution_tag=sol_tag,
                    answer=refined_text,
                    product=products_info if len(products_info) > 1 else products_info[0] if products_info else {"name": None, "category": None, "desc": None, "url": None},
                    price={
                        "in_token": refined["price"]["in_token"]+raw_answer.get_price()["in_token"],
                        "out_token": refined["price"]["out_token"]+raw_answer.get_price()["out_token"],
                        "price": refined["price"]["price"]+raw_answer.get_price()["price"]
                    }
                ))

        return injected_results
