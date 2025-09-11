"""
Solutions package for GemBench

This package contains implementations for detecting and mitigating adversarial ad injection in LLMs.
"""

from .src import AdvocateWorkflow
from .src import ChatbotAdsWorkflow

__all__ = ["AdvocateWorkflow", "ChatbotAdsWorkflow"]