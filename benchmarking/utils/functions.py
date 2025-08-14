import logging
import os
from typing import List, Optional
import nltk
from nltk.tokenize import sent_tokenize
from benchmarking.utils.sentence import Sentence
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
    """Split text into sentences using NLTK tokenizer and filter out short sentences."""
    setup_nltk()
    # First get sentences using NLTK
    sentences = sent_tokenize(content)

    # Filter out short sentences and empty ones
    processed_sentences = []
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        # Skip code blocks and special content
        if (
            sent.startswith("```")
            or sent.startswith("`")
            or sent.startswith("#")
            or sent.startswith(">")
            or sent.startswith("{")
            or sent.startswith("[")
        ):
            continue

        # Filter out short sentences
        if len(sent) > 3:
            processed_sentences.append(sent)

    return processed_sentences

    
        
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
