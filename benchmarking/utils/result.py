from typing import List, Tuple, Optional, Dict, Any, Union
from benchmarking.utils.functions import split_sentences_nltk, get_cosine_similarity
from benchmarking.utils.sentence import Sentence

class Result:
    """
    The result of a single solution for a single data set with a single prompt providing product information.
    It provides the following information:
    - prompt: the prompt
    - category: the category
    - solution_tag: the solution tag
    - content: the content
    - product: the product
    """
    def __init__(self, 
                prompt: str, 
                category: str, 
                solution_tag: str, 
                content: Union[str, Sentence, List[Sentence]] = None,
                product: Optional[Dict] = None):
        """
        Initialize the result object
        
        Args:
            prompt: the prompt
            category: the category
            solution_tag: the solution tag
            content: the content - can be a string, Sentence object or Sentence list
            logprobs: the logprobs
            product: the product information
        """
        self.prompt = prompt
        self.category = category
        self.solution_tag = solution_tag
        self.product = product
        
        if content is None:
            raise ValueError("Content must be provided")
            
        # According to the type of content, initialize the content and sentences
        if isinstance(content, str):
            self.raw_content = content
            self.sentences = [Sentence(s) for s in split_sentences_nltk(content)]
        elif isinstance(content, Sentence):
            self.raw_content = content.to_string()
            self.sentences = [Sentence(s) for s in split_sentences_nltk(content.to_string())]
        elif isinstance(content, list) and all(isinstance(s, Sentence) for s in content):
            self.sentences = content
            self.raw_content = " ".join(s.to_string() for s in content)
        else:
            print("content: ", content)
            print("type(content): ", type(content))
            raise TypeError("Content must be a string, Sentence object, or list of Sentence objects")
        
        # Create content as a Sentence object for backward compatibility
        self.content = Sentence(self.raw_content)
        
        self.metrics = None
        self.adjacent_sentence_similarities = self.calculate_adjacent_sentence_similarities()
        self.ad_indices = self.retrieve_ad_indices()
        
    def get_product(self) -> Dict:
        """Get the product
        
        Returns:
            Dict: the product
        """
        return self.product
    
    def get_prompt(self) -> str:
        """Get the prompt
        
        Returns:
            str: the prompt
        """
        return self.prompt
    
    def get_solution_name(self) -> str:
        """Get the solution name
        
        Returns:
            str: the solution name
        """
        return self.solution_tag
    
    def get_solution_tag(self) -> str:
        """Get the solution tag
        
        Returns:
            str: the solution tag
        """
        return self.solution_tag
    
    def get_raw_response(self) -> str:
        """Get the raw response
        
        Returns:
            str: the content
        """
        return self.raw_content
    
    def get_sentences(self) -> List[Sentence]:
        """Get the sentences
        
        Returns:
            List[Sentence]: the sentences
        """
        return self.sentences
    
    def get_category(self) -> str:
        """Get the category
        
        Returns:
            str: the category
        """
        return self.category
    
    def get_ad_indices(self) -> List[int]:
        """Get the ad index position
        Returns:
            List[int]: the ad index position
        """
        return self.ad_indices
    
    def get_adjacent_sentence_similarities(self) -> List[Tuple[int, int, float]]:
        """Get the similarity between adjacent sentences
        Returns:
            List[Tuple[int, int, float]]: the similarity between adjacent sentences
        """
        return self.adjacent_sentence_similarities

    def retrieve_ad_indices(self) -> List[int]:
        """Get the ad index position
        Returns:
            List[int]: the ad index position
        
        Note:
            If the product is not provided, the ad index position is None.
        For example:
            The output of the model is:
            ```
            The product is a good product.
            The product is a bad product.
            ```
            The ad index position is [1]. Because the second sentence is the ad.
        """
        if self.product is None or self.product.get('name') is None:
            return None
        ad_indices = {i for i, sent in enumerate(self.sentences) 
                    if any(self.product.get(key) in sent.sentence for key in ['name', 'url'])}
        return list(ad_indices)
    
    def calculate_adjacent_sentence_similarities(self) -> List[Tuple[int, int, float]]:
        """Calculate the similarity between adjacent sentences
        
        Returns:
            List[Tuple[int, int, float]]: the similarity between adjacent sentences
        
        Note:
            If the number of sentences is less than 2, the similarity between adjacent sentences is None.
        For example:
            The output of the model is:
            ```
            The product is a good product.
            The product is a bad product.
            ```
            The similarity between adjacent sentences is [(0, 1, 0.95)].
        """
        return [
            (i, i + 1, get_cosine_similarity(
                self.sentences[i].embedding,
                self.sentences[i + 1].embedding
            ))
            for i in range(len(self.sentences) - 1)
        ]

    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON format
        
        Returns:
            Dict[str, Any]: the JSON format
        
        Note:
            The JSON format is as follows:
            {
                'prompt': the prompt,
                'category': the category,
                'solution': the solution tag,
                'content': the content,
                'product': the product
            }
        """
        return {
            'prompt': self.prompt,
            'category': self.category,
            'solution': self.solution_tag,
            'content': self.raw_content,
            'product': self.product
        }
    
    def __str__(self) -> str:
        """String representation
        
        Returns:
            str: the string representation
        
        Note:
            The string representation is as follows:
            Result(tag='solution_tag', content='content_preview', product=product)
        """
        return f"Result(tag='{self.solution_tag}', content='{self.raw_content[:50]}...', product={self.product})"

