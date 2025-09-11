import logging
import os
from typing import List, Optional
import nltk
from nltk.tokenize import sent_tokenize
from .sentence import Sentence
import numpy as np
import re

# Set environment variable to suppress tokenizer parallelism warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# keep track so we only do this once
_nltk_initialized = False

def setup_nltk(nltk_data_dir: Optional[str] = None) -> None:
    """Ensure punkt, stopwords and wordnet corpora are available."""
    global _nltk_initialized
    if _nltk_initialized:
        return
    # if you have a bundled nltk_data directory, add it
    if nltk_data_dir:
        nltk.data.path.append(nltk_data_dir)

    for package, path in [
        ("punkt", "tokenizers/punkt"),
        ("stopwords", "corpora/stopwords"),
        ("wordnet", "corpora/wordnet"),
    ]:
        try:
            nltk.data.find(path)
        except LookupError:
            logging.info(f"NLTK corpus '{package}' not found. Downloading…")
            nltk.download(package, quiet=True)
    _nltk_initialized = True

def split_sentences_nltk(content: str) -> List[str]:
    """
    Split text into sentences using NLTK while treating newlines as hard boundaries.
    - Newlines are preserved and always attached to the *previous* sentence.
    - Consecutive newlines (\\n\\n) are preserved as-is.
    - Short sentences (<=3 visible chars) are filtered out.
    """

    if not content:
        return []

    # Normalize line endings
    text = content.replace("\r\n", "\n").replace("\r", "\n")

    # Split by newlines but keep them
    # Example: "A.\n\nB." -> ["A.", "\n\n", "B."]
    parts = re.split(r'(\n+)', text)

    results: List[str] = []
    buffer = ""  # current sentence being built

    for part in parts:
        if not part:
            continue

        if part.startswith("\n"):
            # newline chunk: always append to buffer
            buffer += part
            continue

        # tokenize the text chunk (without newlines)
        sentences = sent_tokenize(part)
        for sent in sentences:
            if buffer:  # flush previous buffer first
                if len(buffer.strip()) > 3:
                    results.append(buffer)
                buffer = ""

            buffer = sent  # start a new sentence

    # flush last buffer
    if buffer and len(buffer.strip()) > 3:
        results.append(buffer)

    return results
    
        
def get_cosine_similarity(embedding1: Optional[np.ndarray], embedding2: Optional[np.ndarray]) -> float:
    """Compute cosine similarity between two embeddings.
    
    Args:
        embedding1: The first embedding.
        embedding2: The second embedding.
        
    Returns:
        float: The cosine similarity.
    """
    if embedding1 is None or embedding2 is None:
        return 0.0
    
    if not isinstance(embedding1, np.ndarray) or not isinstance(embedding2, np.ndarray):
        return 0.0
        
    if embedding1.size == 0 or embedding2.size == 0:
        return 0.0
        
    dot_product = np.dot(embedding1, embedding2)
    norm_product = np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    
    if norm_product == 0:
        return 0.0
        
    return dot_product / norm_product

from .embedding import Embedding
class SentenceEmbedding(Embedding):
    """Class to handle sentence embeddings"""
    def __init__(self, raw_results: List[str],
                 model_name: str = 'text-embedding-3-small'
                 # model_name: str = "Sentence-Transformers/all-MiniLM-L6-v2"
                 ):
        super().__init__(model_name=model_name)
        self.raw_results = raw_results
        self.splited_result: List[List[str]] = [
            self._split_raw_result(r) for r in raw_results
        ]

    def _split_raw_result(self, raw_result: str) -> List[str]:
        """Split a raw result into sentences"""
        return split_sentences_nltk(raw_result)

    def _get_all_sentences(self) -> List[str]:
        """Flatten to a list of sentences (preserves original order with duplicates)."""
        return [s for group in self.splited_result for s in group]

    def embed(self, dim: int | None = None) -> List[List[Sentence]]:
        """
        Generate embeddings for all sentences in raw_results,
        grouping them per original raw result order (order & duplicates preserved).
        """
        all_sentences = self._get_all_sentences()
        if not all_sentences:
            return [[] for _ in self.splited_result]

        dim = dim or self.model_config['default_dim']

        # encode_all returns List[Tuple[str, List[float]]]
        embeddings_result = self.encode_all(all_sentences, dim=dim)
        
        # Convert to dict for easy lookup
        embeddings_map = {text: embedding for text, embedding in embeddings_result}
        embeddings_list = [embeddings_map[s] for s in all_sentences]

        grouped: List[List[Sentence]] = []
        cursor = 0
        for sentences_in_one in self.splited_result:
            group: List[Sentence] = []
            for _ in sentences_in_one:
                emb = embeddings_list[cursor]
                group.append(Sentence(sentence=all_sentences[cursor],
                                      embedding=np.array(emb, dtype=float)))
                cursor += 1
            grouped.append(group)

        return grouped