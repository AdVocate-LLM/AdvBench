import logging
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from typing import List, Optional
import nltk
from nltk.tokenize import sent_tokenize
from benchmarking.utils.sentence import Sentence
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re

# Set environment variable to suppress tokenizer parallelism warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

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


def split_sentences_nltk(text: Optional[str]) -> List[str]:
    """Split a text into sentences using NLTK.
    
    Args:
        text: The text to split.
        
    Returns:
        List[str]: A list of sentences.
    """
    setup_nltk()
    if not text or not isinstance(text, str):
        return []
    
    try:
        import nltk
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        sentences = sent_tokenize(text)
        return [s.strip() for s in sentences if s.strip()]
    except Exception as e:
        print(f"Error splitting sentences: {e}")
        if not text:
            return []
            
        import re
        sentences = re.split(r'[.!?]\s+', text)
        if text and not text.rstrip().endswith(('.', '!', '?')):
            last_part = text.split('.')[-1].split('!')[-1].split('?')[-1].strip()
            if last_part and last_part not in sentences:
                sentences.append(last_part)
        return [s.strip() for s in sentences if s.strip()]


def split_sentences_regex(content: str) -> List[Sentence]:
    try:
        # Normalize line endings and remove excessive whitespace
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        content = re.sub(r'\n\s*\n', '\n\n', content)  # Normalize multiple newlines
        lines = content.split('\n')
        processed_blocks = []
        current_block = []

        # First pass: Group lines into logical blocks
        for line in lines:
            line = line.strip()
            # Skip empty lines, very short lines, and standalone numbers
            if (not line or 
                len(line) < 2 or 
                re.match(r'^\d+\.$', line) or  # Standalone numbers like "1."
                re.match(r'^\d+$', line)):     # Just numbers
                if current_block:
                    processed_blocks.append(' '.join(current_block))
                    current_block = []
                continue

            # Check for special block starts
            if (re.match(r'^```|^`', line) or              # Code blocks
                re.match(r'^\{|^\[', line) or              # JSON/array blocks
                re.match(r'^#+\s+', line) or               # Markdown headers
                re.match(r'^>', line) or                   # Blockquotes
                re.match(r'^\s*[-*]\s+', line)):          # Markdown lists
                if current_block:
                    processed_blocks.append(' '.join(current_block))
                current_block = [line]
            else:
                current_block.append(line)

        if current_block:
            processed_blocks.append(' '.join(current_block))

        # Second pass: Split blocks into sentences
        sentences = []
        for block in processed_blocks:
            # Handle special blocks
            if (block.startswith('```') or block.startswith('`') or
                block.startswith('{') or block.startswith('[') or
                block.startswith('#') or block.startswith('>')):
                sentences.append(block)
                continue

            # Split into sentences using regex
            # This pattern looks for sentence endings followed by whitespace and capital letter
            # but avoids splitting inside quotes or parentheses
            parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'])', block)
            
            # Further refine splits for edge cases
            refined_parts = []
            for part in parts:
                part = part.strip()
                # Skip empty, very short parts, or standalone numbers
                if (not part or 
                    len(part) < 2 or 
                    re.match(r'^\d+\.$', part) or  # Standalone numbers like "1."
                    re.match(r'^\d+$', part)):     # Just numbers
                    continue
                    
                # Handle abbreviations and common edge cases
                if re.match(r'^[A-Z]\.\s*[A-Z]', part):  # Abbreviations like "U.S."
                    refined_parts.append(part)
                elif re.match(r'^[0-9]+\.\s*[0-9]+', part):  # Version numbers like "1.0"
                    refined_parts.append(part)
                else:
                    refined_parts.append(part)
            
            sentences.extend(refined_parts)

        # Filter out empty or invalid sentences
        return [Sentence(s) for s in sentences if len(s.strip()) > 1]

    except Exception as e:
        logging.error(f"Sentence splitting failed: {str(e)}")
        return [Sentence(content)]

        
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
    
    try:
        # 确保数据类型和维度正确
        if not isinstance(embedding1, np.ndarray) or not isinstance(embedding2, np.ndarray):
            return 0.0
            
        if embedding1.size == 0 or embedding2.size == 0:
            return 0.0
            
        # 计算余弦相似度
        dot_product = np.dot(embedding1, embedding2)
        norm_product = np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        
        if norm_product == 0:
            return 0.0
            
        return dot_product / norm_product
    except Exception as e:
        print(f"Error computing cosine similarity: {e}")
        return 0.0