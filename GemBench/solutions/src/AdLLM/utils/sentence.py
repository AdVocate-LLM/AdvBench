import numpy as np
class Sentence:
    """Class representing a sentence with its embedding"""
    def __init__(self, sentence: str, embedding: np.ndarray):
        self.sentence = sentence
        self.embedding = embedding
        
    def get_embedding(self) -> np.ndarray:
        """Get embedding for the sentence"""
        return self.embedding
    
    def __str__(self) -> str:
        """String representation of the sentence"""
        return f"Sentence(sentence='{self.sentence[:50]}...')"
    
    def to_string(self) -> str:
        """String representation of the sentence"""
        return self.sentence