
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Optional
from .sentence import Sentence
import logging
import nltk
from nltk.tokenize import sent_tokenize
import re


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


from .embedding import Embedding
class SentenceEmbedding:
    """Class to handle sentence embeddings"""

    def __init__(self, raw_results: List[str],
                emb_model: Embedding):
        self.emb_model = emb_model
        self.raw_results = raw_results
        self.splited_result: List[List[str]] = [
            self._split_raw_result(raw_result) for raw_result in raw_results
        ]

    def _split_raw_result(self, raw_result: str) -> List[str]:
        """Split a raw result into sentences"""
        return split_sentences_nltk(raw_result)
    
    def _get_all_sentences(self) -> List[str]:
        """Transform splited_result into a list of sentences"""
        return [sentence for raw_result in self.splited_result for sentence in raw_result]

    def embed(self) -> List[Tuple[List[Sentence], List[int]]]:
        """
        Generate embeddings for all sentences in raw_results,
        grouping them per original raw result order.

        :param sentences: unused; embeddings are generated from raw_results
        :return: List of lists of tuple(Sentence, List[int])
        """
        # Flatten all sentences and compute embeddings in a batch
        all_sentences = self._get_all_sentences()
        # Encode while preserving order (avoid key collisions for duplicate sentences)
        if all_sentences:
            embeddings_map = self.emb_model.encode_all(all_sentences)
            embeddings_list = [embedding[1] for embedding in embeddings_map]
        else:
            embeddings_list = []

        output: List[Tuple[List[Sentence], List[int]]] = []
        global_idx = 0
        for i in range(len(self.splited_result)):
            sentences_i = self.splited_result[i]

            # Build Sentence objects with embeddings in original order
            results: List[Sentence] = []
            for _s in sentences_i:
                if global_idx < len(embeddings_list):
                    emb = embeddings_list[global_idx]
                else:
                    exit()
                    emb = [0.0] * self.emb_model.model_config['default_dim']
                results.append(Sentence(sentence=_s, embedding=np.array(emb, dtype=float)))
                global_idx += 1

            # Build structure as sentence indices (much faster than character position search)
            # Since we now use sentence indices directly in injection, we don't need character positions
            end_indices: List[int] = list(range(len(sentences_i)))

            structure = end_indices
            output.append((results, structure))
        return output