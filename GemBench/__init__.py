"""
GemBench: A comprehensive framework for detecting and mitigating adversarial ad injection in LLMs

This package provides:
- Solutions for ad injection detection and mitigation (AdLLMWorkflow, AdChatWorkflow)  
- Benchmarking framework for evaluating ad injection detection techniques (GemBench)
- Utility functions for text processing and analysis
"""

__version__ = "0.1.0"
__author__ = "GemBench Team"

# Import main classes for easy access
from .solutions.src.AdLLM import AdLLMWorkflow
from .solutions.src.AdChat import AdChatWorkflow
from .benchmarking import GemBench, GemDatasets, ModelPricing

# Import utility functions
from .benchmarking import split_sentences_nltk
from .solutions.src.AdLLM.config import *

# Analysis
from .benchmarking import EvaluationResult

# Product dataset
from .benchmarking.dataset import PRODUCT_DATASET_PATH, TOPIC_DATASET_PATH

# Tools
from .benchmarking.tools.ModelPrice import ModelPricing

# Define public API
__all__ = [
    # Main workflow classes
    "AdLLMWorkflow",
    "AdChatWorkflow", 
    "GemBench",
    
    # Dataset and utilities
    "GemDatasets",
    "ModelPricing",
    
    # Tools
    "ModelPricing",
    
    # Utility functions
    "split_sentences_nltk",
    
    # Configuration constants
    "LINEAR_WEIGHT",
    "LOG_WEIGHT",
    
    # Analysis
    "EvaluationResult",
    
    # Product dataset
    "PRODUCT_DATASET_PATH",
    "TOPIC_DATASET_PATH",
]

# Package metadata
__title__ = "GemBench"
__description__ = "A comprehensive framework for detecting and mitigating adversarial ad injection in LLMs"
__url__ = "https://github.com/AdVocate-LLM/GEM-Bench"
__license__ = "MIT"