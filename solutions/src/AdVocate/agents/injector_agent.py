from ..utils.oracle import Oracle
from ..utils.result import Result
from ..utils.sentence import Sentence
from ..utils.product import Product
from ..utils.functions import get_adjacent_sentence_similarities, split_sentences_nltk
from ..utils.format import sentence_list2string
from typing import List, Tuple, Optional, Dict, Any
from ..prompt.injector_prompts import SYS_REFINE, USER_REFINE
from .base_agent import BaseAgent
# import tools for injector agent
from ..tools.productRAG import productRAG
from ..tools.injector import Injector
from sentence_transformers import SentenceTransformer

class InjectorAgent(BaseAgent):
    # enum for productRAG
    DEFAULT_RAG_MODEL = 'all-MiniLM-L6-v2'
    ADS_START = "[[ADS_START]]"
    ADS_END = "[[ADS_END]]"
    
    # enum for injection methods
    QUERY_PROMPT = "QUERY_PROMPT"
    QUERY_RESPONSE = "QUERY_RESPONSE"
    QUERY_PROMPT_N_RESPONSE = "QUERY_PROMPT_N_RESPONSE"
    
    # enum for refine methods
    REFINE_GEN_INSERT = 'REFINE_GEN_INSERT'
    BASIC_GEN_INSERT = 'BASIC_GEN_INSERT'
    
    def __init__(self, 
                model: Oracle, 
                product_list_path: str,
                rag_model: Optional[SentenceTransformer] = None
                ) -> None:
        super().__init__(model)
        # basic settings
        self.product_list_path = product_list_path
        self.rag_model = rag_model or SentenceTransformer(self.DEFAULT_RAG_MODEL)
        self.system_prompt = SYS_REFINE
        
        self.INJECT_METHODS = {
            "QUERY_PROMPT": self.QUERY_PROMPT, 
            "QUERY_RESPONSE": self.QUERY_RESPONSE, 
            "QUERY_PROMPT_N_RESPONSE": self.QUERY_PROMPT_N_RESPONSE
        }
        
        self.REFINE_METHODS = {
            "REFINE": self.REFINE_GEN_INSERT,
            "BASIC": self.BASIC_GEN_INSERT
        }
        
        # Initialize the tools
        self.product_rag = productRAG(
            file_path=self.product_list_path,
            model=self.rag_model
        )
        self.injector = Injector()

    def get_inject_methods(self) -> Dict[str, str]:
        """Get available injection methods.
        
        Returns:
            Dict[str, str]: Dictionary of injection methods
        """
        return self.INJECT_METHODS

    def refine_content(self, content: str, logprobs: bool = True) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Refine the given content using the language model.
        
        Args:
            content (str): The content to be refined
            logprobs (bool): Whether to return log probabilities
            
        Returns:
            Tuple[str, Optional[Dict[str, Any]]]: Refined text and log probabilities if requested
        """
        usr_refine_ass = USER_REFINE.format(ori_text=content)
        response = self.model.query(SYS_REFINE, usr_refine_ass, logprobs=logprobs)
        refined_text = response["answer"]
        if logprobs:
            return refined_text, response["logprobs"]
        else:
            return refined_text, None

    def create_refined_injection(self, 
                            raw_answer: Result,
                            sol_tag: str,
                            sentences: List[Sentence], 
                            inject_position: Tuple[int, int], 
                            best_product: Product) -> Result:
        """Create a refined injection by inserting and optimizing the product.
        
        Args:
            raw_answer (Result): Original answer
            sentences (List[Sentence]): List of sentences
            inject_position (Tuple[int, int]): Position to inject the product
            best_product (Product): Product to inject
            
        Returns:
            Result: Refined result with injected product
        """
        product_text = f"{self.ADS_START}{str(best_product)}{self.ADS_END}"
        product_sentence = Sentence(product_text, self.rag_model)
        new_sentences = sentences[:inject_position[0]+1] + [product_sentence] + sentences[inject_position[1]:]
        content = sentence_list2string(new_sentences)
        
        refined_text, logprobs = self.refine_content(content)
        refined_result = Result(
            prompt=raw_answer.get_prompt(),
            solution_tag=sol_tag,
            answer=refined_text,
            logprobs=logprobs,
            product=best_product.show()
        )

        return refined_result
    
    def create_basic_injection(self, 
                            raw_answer: Result, 
                            sol_tag: str,
                            sentences: List[Sentence], 
                            inject_position: Tuple[int, int], 
                            best_product: Product) -> Result:
        """Create a basic injection by inserting the product without optimization.
        
        Args:
            raw_answer (Result): Original answer
            sentences (List[Sentence]): List of sentences
            inject_position (Tuple[int, int]): Position to inject the product
            best_product (Product): Product to inject
            
        Returns:
            Result: Result with injected product
        """
        product_text = str(best_product)
        product_sentence = Sentence(product_text, self.rag_model)
        new_sentences = sentences[:inject_position[0]+1] + [product_sentence] + sentences[inject_position[1]:]
        injected_result = Result(
            prompt=raw_answer.get_prompt(),
            solution_tag=sol_tag,
            answer=sentence_list2string(new_sentences),
            product=best_product.show()
        )
        return injected_result
    
    def get_query_text(self, raw_answer: Result, query_type: str) -> str:
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
        products = self.product_rag.query(query, top_k=5)
        # convert the sentences to sentences
        sentences = split_sentences_nltk(raw_answer.get_answer(), self.rag_model)
        sentence_flow = get_adjacent_sentence_similarities(sentences)
        best_product, prev_pos, next_pos, disrupt = self.injector.get_best_inject_product(
            sentences, sentence_flow, products
        )
        
        # Step 2: Inject the best product based on the solution
        sol_tag = f'{solution_name}_{query_type}'
        # only inject the product without optimization
        if solution_name == self.BASIC_GEN_INSERT:
            return self.create_basic_injection(
                raw_answer, sol_tag, sentences, (prev_pos, next_pos), best_product
            )
        # inject the product and optimize the content
        elif solution_name == self.REFINE_GEN_INSERT:
            return self.create_refined_injection(
                raw_answer, sol_tag, sentences, (prev_pos, next_pos), best_product
            )
    
    def inject_products(self, 
                    raw_answers: List[Result],
                    query_type: str = QUERY_RESPONSE,
                    solution_name: str = REFINE_GEN_INSERT,
                    batch_size=5,
                    max_retries=2,
                    timeout=180) -> List[Result]:
        """Inject products into the answers at optimal positions with optimized parallel processing.
        
        Args:
            raw_answers (List[Result]): List of raw answers
            query_type (str): Type of query to use | QUERY_PROMPT, QUERY_RESPONSE, QUERY_PROMPT_N_RESPONSE
            solution_name (str): Name of the solution to use | BASIC_GEN_INSERT, REFINE_GEN_INSERT
            batch_size (int): Size of batches for improved performance.
            max_retries (int): Maximum retry attempts for failed injections.
            timeout (int): Timeout in seconds for each process.
            
        Returns:
            List[Result]: List of results with injected products
        """
        # Use the parallel processor base class
        def process_func(raw_answer, query_type=query_type, solution_name=solution_name):
            return self.inject_products_single(raw_answer, query_type, solution_name)
        
        return self.parallel_process(
            items=raw_answers,
            process_func=process_func,
            workers=None,
            batch_size=batch_size,
            max_retries=max_retries,
            timeout=timeout,
            task_description="Injecting products"
        )