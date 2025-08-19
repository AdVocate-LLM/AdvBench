
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Union, Optional
from .sentence import Sentence
import logging
import nltk
from nltk.tokenize import sent_tokenize, PunktSentenceTokenizer
from sentence_transformers import SentenceTransformer


def get_adjacent_sentence_similarities(
    sentences: List[Sentence],
) -> List[Tuple[int, int, float]]:
    """Calculate similarities between adjacent sentences"""
    return [
        (
            i,
            i + 1,
            get_cosine_similarity(sentences[i].embedding, sentences[i + 1].embedding),
        )
        for i in range(len(sentences) - 1)
    ]


def get_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors using scikit-learn"""
    # Handle None values
    if vec1 is None or vec2 is None:
        logging.warning("One or both vectors are None, returning 0.0")
        return 0.0

    try:
        # Ensure data types and dimensions are correct
        if not isinstance(vec1, np.ndarray) or not isinstance(vec2, np.ndarray):
            logging.warning("One or both inputs are not numpy arrays, returning 0.0")
            return 0.0

        if vec1.size == 0 or vec2.size == 0:
            logging.warning("One or both vectors are empty, returning 0.0")
            return 0.0

        vec1_2d = vec1.reshape(1, -1)
        vec2_2d = vec2.reshape(1, -1)
        similarity = cosine_similarity(vec1_2d, vec2_2d)[0][0]
        return max(0.0, min(1.0, similarity))
    except Exception as e:
        logging.error(f"Error calculating cosine similarity: {str(e)}")
        return 0.0


def evaluate_global_coherence(sentences: List[Sentence]):
    """Calculate global coherence score using sentence embeddings"""
    if len(sentences) < 2:
        return None

    mean_embedding = np.mean([sent.embedding for sent in sentences], axis=0)
    similarities = [
        get_cosine_similarity(sent.embedding, mean_embedding) for sent in sentences
    ]
    return np.mean(similarities)
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