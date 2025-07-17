import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple, Union, Optional
from .sentence import Sentence
import logging
import nltk
import os
from nltk.tokenize import sent_tokenize, PunktSentenceTokenizer


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


def split_sentences_with_template(
    content: str, rag_model
) -> Tuple[List[Sentence], List[Union[str, int]]]:
    """Split text into sentences and non-sentence parts while preserving structure."""
    setup_nltk()

    # Use PunktSentenceTokenizer directly to get spans
    tokenizer = PunktSentenceTokenizer()
    spans = list(tokenizer.span_tokenize(content))

    # Process content and build structure
    processed_sentences = []
    structure = []
    last_end = 0

    for start, end in spans:
        sent = content[start:end].strip()
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
            # Add preceding non-sentence content
            preceding_content = content[last_end:start]
            if preceding_content:
                structure.append(preceding_content)

            # Add sentence index
            sentence_obj = Sentence(sent, rag_model)
            processed_sentences.append(sentence_obj)
            structure.append(len(processed_sentences) - 1)

            last_end = end

    # Add remaining non-sentence content after last sentence
    remaining_content = content[last_end:]
    if remaining_content:
        structure.append(remaining_content)

    return processed_sentences, structure


def split_sentences_nltk(content: str, rag_model) -> List[Sentence]:
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

    return [Sentence(s, rag_model) for s in processed_sentences]
