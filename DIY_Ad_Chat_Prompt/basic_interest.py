"""
Basic Interest Strategy - Simple Product-Based Advertising
基础兴趣策略 - 简单的产品推荐广告

Strategy: Subtly integrate product mentions when timing/topic is relevant
Focus: Product relevance without user profiling
"""

from .adchat_prompts import (
    SYS_INTEREST,
    SYS_RELEVANT_PRODUCT
)

# Product selection prompt - based on prompt only (no user demographics)
SELECTION_PROMPT = SYS_RELEVANT_PRODUCT

# Response generation prompt - basic helpful response with product mention
RESPONSE_PROMPT = SYS_INTEREST
