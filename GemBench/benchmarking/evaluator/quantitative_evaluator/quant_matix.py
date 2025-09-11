from typing import List, Tuple, Optional
import numpy as np
from math import exp
from ...utils.sentence import Sentence
from ...utils.functions import get_cosine_similarity

# global metrics
def evaluate_local_flow(adjacent_similarities: List[Tuple[int, int, float]]) -> Optional[float]:
    """
    Among all the adjacent sentence similarities, calculate the average similarity.
    Attempt to calculate the average similarity of the adjacent sentences.
    
    Args:
        adjacent_similarities: List of (i, j, similarity) tuples for adjacent sentences
        
    Returns:
        float: The average similarity of the adjacent sentences (0-100 scale)
        
    Note:
        This is as high as possible.
        This means fluency of the response.
        
    Formula:
        local_flow = (1/n) * Σ sim(i, i+1) for all adjacent sentences
        
    Example:
        If we have similarities [(0,1,0.8), (1,2,0.7), (2,3,0.9)],
        local_flow = (0.8 + 0.7 + 0.9) / 3 = 0.8
        Converted to percentage: 0.8 * 100 = 80
    
    What is this metric means for Gem LLM response:
        When the LLM response is not fluent, the adjacent sentence similarities will be low.
        When the LLM response is fluent, the adjacent sentence similarities will be high.
    """
    if not adjacent_similarities:
        return None
        
    similarities = [sim for _, _, sim in adjacent_similarities]
    
    # Convert to percentage (0-100 scale)
    return np.mean(similarities) * 100

def evaluate_global_coherence(sentences: List[Sentence]) -> float:
    """
    Calculate the global coherence score using sentence embeddings.
    
    Args:
        sentences: List of Sentence objects
        
    Returns:
        float: The global coherence score (0-100 scale)
        
    Note:
        This is as high as possible.
        This means coherence of the response.(Means all sentences are related to the center topic.)
    
    Formula:
        1. Calculate mean embedding: E_mean = (1/n) * Σ E_i for all sentences
        2. Calculate similarity of each sentence to mean: sim(E_i, E_mean)
        3. global_coherence = (1/n) * Σ sim(E_i, E_mean)
        
    Example:
        If we have 3 sentences with similarities to mean [0.85, 0.78, 0.92],
        global_coherence = (0.85 + 0.78 + 0.92) / 3 = 0.85
        Converted to percentage: 0.85 * 100 = 85
    
    What is this metric means for Gem LLM response:
        When the LLM response is not coherent, the global coherence score will be low.
        When the LLM response is coherent, the global coherence score will be high.
    """
    if len(sentences) < 2:
        return None
        
    mean_embedding = np.mean([sent.embedding for sent in sentences], axis=0)
    similarities = [
        get_cosine_similarity(sent.embedding, mean_embedding)
        for sent in sentences
    ]
    # Convert to percentage (0-100 scale)
    return np.mean(similarities) * 100

# local metrics
def evaluate_ad_transition_similarity(
    adjacent_similarities: List[Tuple[int, int, float]], 
    ad_indices: List[int]) -> Optional[float]:
    """Calculate the average similarity score for ad transitions
    
    Args:
        adjacent_similarities: List of (i, j, similarity) tuples for adjacent sentences
        ad_indices: List of indices for ad-containing sentences
        
    Returns:
        float: Average similarity score for ad transitions (0-100 scale)
        
    Note:
        This is as high as possible.
        This means the ad transitions are smooth.
        
    Formula:
        1. For each ad sentence i, find sim(i-1, i) and sim(i, i+1)
        2. Take min(sim(i-1, i), sim(i, i+1)) as the transition score
        3. ad_transition = (1/m) * Σ transition_scores for all m ad sentences
        
    Example:
        If ad_indices = [2, 5] and we have transitions:
        sim(1,2) = 0.7, sim(2,3) = 0.6, sim(4,5) = 0.8, sim(5,6) = 0.5
        Transition scores: min(0.7, 0.6) = 0.6, min(0.8, 0.5) = 0.5
        ad_transition = (0.6 + 0.5) / 2 = 0.55
        Converted to percentage: 0.55 * 100 = 55
    
    What is this metric means for Gem LLM response:
        When the LLM response inserts ads in a non-smooth way, the ad transitions will be low.
        When the LLM response inserts ads in a smooth way, the ad transitions will be high.
    """
    if not adjacent_similarities or not ad_indices:
        return None

    # Calculate average similarity score for ad transitions
    ad_transition_similarities = []
    for i in ad_indices:
        # Find similarities with previous and next sentences
        prev_sim = next((sim for j, k, sim in adjacent_similarities if k == i), 0.0)
        next_sim = next((sim for j, k, sim in adjacent_similarities if j == i), 0.0)
        if prev_sim > 0 and next_sim > 0:
            # Take the minimum similarity as the bottleneck for smoothness
            ad_transition_similarities.append(exp(-abs(prev_sim - next_sim)))
    
    # Convert to percentage (0-100 scale)
    return np.mean(ad_transition_similarities) * 100 if ad_transition_similarities else 0.0

def evaluate_ad_content_alignment(
        sentences: List[Sentence], 
        ad_indices: List[int]) -> Optional[float]:
    """Calculate similarity between ad sentences and non-ad content center
    
    Args:
        sentences: List of Sentence objects
        ad_indices: List of indices for ad-containing sentences
        
    Returns:
        float: Average similarity between ad sentences and non-ad content center (0-100 scale)
    
    Note:
        This is as high as possible.
        This means the ad sentences are aligned with the non-ad content center.
        
    Formula:
        1. Calculate non-ad center: E_non_ad = (1/k) * Σ E_j for all non-ad sentences j
        2. For each ad sentence i, calculate sim(E_i, E_non_ad)
        3. ad_alignment = (1/m) * Σ sim(E_i, E_non_ad) for all m ad sentences
        
    Example:
        If ad_indices = [1, 3] in a 5-sentence text:
        1. Calculate center of sentences 0, 2, 4
        2. Calculate similarities: sim(sent1, center) = 0.75, sim(sent3, center) = 0.82
        3. ad_alignment = (0.75 + 0.82) / 2 = 0.785
        Converted to percentage: 0.785 * 100 = 78.5
    
    What is this metric means for Gem LLM response:
        When the LLM response inserts ads in a non-aligned way, the ad content alignment will be low.
        When the LLM response inserts ads in a aligned way, the ad content alignment will be high.
    """
    if not sentences or not ad_indices or len(sentences) <= len(ad_indices):
        return None
        
    # Get non-ad sentence embeddings
    non_ad_embeddings = [sent.embedding for i, sent in enumerate(sentences) if i not in ad_indices]
    non_ad_center = np.mean(non_ad_embeddings, axis=0)
    
    # Calculate similarity between ad sentences and non-ad center
    ad_alignments = [
        get_cosine_similarity(sentences[i].embedding, non_ad_center)
        for i in ad_indices
    ]
    
    # Convert to percentage (0-100 scale)
    return np.mean(ad_alignments) * 100 if ad_alignments else None