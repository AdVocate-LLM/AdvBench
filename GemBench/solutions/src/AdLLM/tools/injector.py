from typing import List, Tuple, Callable, Optional
from ..utils.product import Product
from ..utils.sentence import Sentence
import numpy as np
from ..config import *

class Injector:
    def __init__(self, score_func: str = LOG_WEIGHT):
        self.score_func = score_func
        if self.score_func == LOG_WEIGHT:
            self.score_func = self._default_score_func_log_weight
        elif self.score_func == LINEAR_WEIGHT:
            self.score_func = self._default_score_func_linear
        else:
            raise ValueError(f"Invalid score function: {self.score_func}")
    
    def _default_score_func_linear(self, inject_flow: float, sim: float) -> float:
        return sim - inject_flow
    
    def _default_score_func_log_weight(self, inject_flow: float, sim: float, alpha: float = 2.0, epsilon: float = 1e-6) -> float:
        """Default scoring function for injection position selection.
        
        Args:
            inject_flow: The flow score between product and adjacent sentences
            sim: The similarity between adjacent sentences
            alpha: Weight factor for similarity in log term (default: 2.0)
            epsilon: Small constant to prevent division by zero (default: 1e-6)
            
        Returns:
            float: Disruption score - lower is better for injection
            
        The scoring function considers:
        1. Flow preservation: (1 - inject_flow/(sim+ε)) term
        - Maximizes inject_flow
        - Minimizes difference between inject_flow and sim
        2. Flow quality: log(1 + α * sim) term
        - Prefers breaking poor flows over good ones
        - α controls sensitivity to flow quality
        """
        flow_preservation = 1 - inject_flow / (sim + epsilon)
        flow_quality = np.log(1 + alpha * sim)
        return flow_preservation * flow_quality
    

    def get_best_inject_position(self, sentences: List[Sentence], sentence_flow: List[Tuple[int, int, float]], 
                            product: Product) -> Tuple[int, int, float]:
        """Find the best position to inject a product advertisement.
        
        Args:
            sentences: List of sentences in the text
            sentence_flow: List of (i, j, similarity) tuples for adjacent sentences
            product: Product to inject
            
        Returns:
            Tuple[int, int, float]: (prev_pos, next_pos, disrupt_score)
        """
        inject_positions: List[Tuple[int, int, float]] = []
        
        # Handle case with no adjacent sentences (single sentence or empty)
        if not sentence_flow:
            if len(sentences) == 0:
                # No sentences, inject at position 0
                return 0, 0, 0.0
            elif len(sentences) == 1:
                # Single sentence, inject after it (position 0 to 1)
                return 0, 1, 0.0
            else:
                # Fallback for unexpected case
                return 0, 1, 0.0
        
        for i, j, sim in sentence_flow:
            prev = sentences[i]
            next = sentences[j]
            # Calculate average flow between product and adjacent sentences
            inject_flow = (product.query(prev.embedding) + product.query(next.embedding)) / 2
            # Calculate disruption score using configured scoring function
            disrupt = self.score_func(inject_flow, sim)
            inject_positions.append((i, j, disrupt))

        # Find position with minimum disruption score
        prev_pos, next_pos, disrupt = min(inject_positions, key=lambda x: x[2])
        return prev_pos, next_pos, disrupt

    def get_best_inject_product(self, sentences: List[Sentence], sentence_flow: List[Tuple[int, int, float]], 
                            products: List[Product]) -> Tuple[Product, int, int, float]:
        """Find the best product and position to inject.
        
        Args:
            sentences: List of sentences in the text
            sentence_flow: List of (i, j, similarity) tuples for adjacent sentences
            products: List of candidate products
            
        Returns:
            Tuple[Product, int, int, float]: (best_product, prev_pos, next_pos, disrupt_score)
        """
        candidate_products: List[Tuple[Product, int, int, float]] = []
        
        for product in products:
            prev_pos, next_pos, disrupt = self.get_best_inject_position(sentences, sentence_flow, product)
            candidate_products.append((product, prev_pos, next_pos, disrupt))
            
        best_product, prev_pos, next_pos, disrupt = min(candidate_products, key=lambda x: x[3])
        return best_product, prev_pos, next_pos, disrupt
    
    def inject(self, sentences: List[Sentence], sentence_flow: List[Tuple[int, int, float]], 
            products: List[Product]) -> List[Sentence]:
        """Inject the best product at the optimal position.
        
        Args:
            sentences: List of sentences in the text
            sentence_flow: List of (i, j, similarity) tuples for adjacent sentences
            products: List of candidate products
            
        Returns:
            List[Sentence]: Updated list of sentences with injected product
        """
        best_product, prev_pos, next_pos, _ = self.get_best_inject_product(sentences, sentence_flow, products)
        sentences.insert(next_pos, best_product.show())
        return sentences