import numpy as np
class Sentence:
    def __init__(self, sentence: str, 
                embedding:np.ndarray
                ):
        self.sentence = sentence
        self.embedding = embedding
    
    def __str__(self) -> str:
        """String representation of the sentence"""
        return f"Sentence(sentence='{self.sentence[:50]}...')"
    
    def to_string(self) -> str:
        """String representation of the sentence"""
        return self.sentence