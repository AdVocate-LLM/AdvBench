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
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            nltk.download('punkt_tab')
        
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
