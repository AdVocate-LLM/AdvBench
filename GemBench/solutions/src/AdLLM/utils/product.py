from typing import Dict, Optional
import numpy as np
from .functions import get_cosine_similarity
class Product:
    def __init__(self, name: str, description: str, category: str, url: str, embedding: Optional[np.ndarray] = None):
        self.name = name
        self.category = category
        self.description = description
        self.url = url
        self.embedding = embedding
        self.has_embedding = embedding is not None

    def query(self, query_embedding:np.ndarray):
        if not self.has_embedding:
            raise ValueError("Embedding not found for product")
        return get_cosine_similarity(self.embedding, query_embedding)
    
    def update_embedding(self, embedding: np.ndarray):
        self.embedding = embedding
        self.has_embedding = True

    def show(self):
        return {
            "name": self.name,
            "category": self.category,
            "desc": self.description,
            "url": self.url
        }

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'url': self.url,
            'category': self.category,
            'embedding': self.embedding.tolist() if self.embedding is not None else None
        }

    @classmethod
    def from_dict(cls, data: Dict, model) -> 'Product':
        embedding = np.array(data['embedding']) if data['embedding'] is not None else None
        return cls(
            name=data['name'],
            description=data['description'],
            category=data['category'],
            url=data['url'],
            model=model,
            embedding=embedding
        )

    def __str__(self) -> str:
        desc = self.description.rstrip('.')
        return f"{self.name}: {desc}."
    
    def ad_content(self) -> str:
        """Generate ad content for the product."""
        desc = self.description.rstrip('.')
        return f"[{self.name}]({self.url}):{desc}."
