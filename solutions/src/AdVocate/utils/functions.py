import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Tuple
from .sentence import Sentence
import logging
import nltk
import os
from nltk.tokenize import sent_tokenize


def get_adjacent_sentence_similarities(sentences: List[Sentence]) -> List[Tuple[int, int, float]]:
    """Calculate similarities between adjacent sentences"""
    return [
            (i, i + 1, get_cosine_similarity(
                sentences[i].embedding,
                sentences[i + 1].embedding
            ))
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

def evaluate_global_coherence(sentences: List[Sentence]) -> float:
    """Calculate global coherence score using sentence embeddings"""
    if len(sentences) < 2:
        return None
        
    mean_embedding = np.mean([sent.embedding for sent in sentences], axis=0)
    similarities = [
        get_cosine_similarity(sent.embedding, mean_embedding)
        for sent in sentences
    ]
    return np.mean(similarities)

def setup_nltk() -> None:
    """Set up NLTK with error handling"""
    try:
        nltk_dir = os.path.join(os.path.dirname(__file__), 'nltk_data')
        if os.path.exists(nltk_dir):
            nltk.data.path.append(nltk_dir)
            logging.info(f"Added NLTK data directory: {nltk_dir}")
            
            # Check and download required NLTK data if missing
            # Skip wordnet due to compatibility issues with some NLTK versions
            required_packages = ['punkt', 'stopwords']
            for package in required_packages:
                try:
                    # Try to use the package to verify it exists
                    if package == 'punkt':
                        sent_tokenize('Test sentence.')
                    elif package == 'stopwords':
                        nltk.corpus.stopwords.words('english')
                except LookupError:
                    logging.info(f"Downloading missing NLTK package: {package}")
                    nltk.download(package, quiet=True)
                except Exception as e:
                    logging.warning(f"Error verifying NLTK package {package}: {e}")
                    # Try to download anyway
                    try:
                        nltk.download(package, quiet=True)
                        logging.info(f"Downloaded NLTK package: {package}")
                    except Exception as download_error:
                        logging.error(f"Failed to download NLTK package {package}: {download_error}")
            
            # For wordnet, just try to download without verification
            try:
                nltk.data.find('corpora/wordnet')
                logging.info("WordNet corpus data found")
            except LookupError:
                try:
                    logging.info("Downloading WordNet corpus data")
                    nltk.download('wordnet', quiet=True)
                except Exception as e:
                    logging.warning(f"Could not download WordNet: {e}")
            except Exception as e:
                logging.warning(f"WordNet check failed: {e}")
            
            logging.info("Successfully verified/loaded all required NLTK data")
        else:
            # If no local nltk_data directory, just try to download required packages
            logging.warning(f"NLTK data directory not found at: {nltk_dir}")
            logging.info("Attempting to download required NLTK packages")
            
            required_packages = ['punkt', 'stopwords', 'wordnet']
            for package in required_packages:
                try:
                    nltk.download(package, quiet=True)
                    logging.info(f"Downloaded NLTK package: {package}")
                except Exception as e:
                    logging.warning(f"Could not download NLTK package {package}: {e}")
                
    except Exception as e:
        logging.error(f"Error setting up NLTK: {str(e)}")
        # Don't raise the exception, just log it to allow the program to continue
        logging.warning("Continuing without complete NLTK setup")
    
def split_sentences_nltk(content: str, rag_model) -> List[Sentence]:
    """Split text into sentences using NLTK tokenizer and filter out short sentences."""
    try:
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
            if (sent.startswith('```') or sent.startswith('`') or
                sent.startswith('#') or sent.startswith('>') or
                sent.startswith('{') or sent.startswith('[')):
                continue
                
            # Filter out short sentences
            if len(sent) > 3:
                processed_sentences.append(sent)
        
        return [Sentence(s, rag_model) for s in processed_sentences]
        
    except Exception as e:
        logging.error(f"Sentence splitting failed: {str(e)}")
        return [Sentence(content, rag_model)]
