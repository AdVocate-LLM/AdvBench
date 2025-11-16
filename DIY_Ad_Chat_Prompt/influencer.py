"""
Influencer Strategy - Detailed Demographics + AI Persona
影响者策略 - 详细人口统计+AI人格

Strategy: Combine detailed user demographics with AI persona
Focus: Maximum personalization using all available user data
"""

from .adchat_prompts import (
    SYS_INFLUENCER_INTEREST,
    SYS_RELEVANT_PRODUCT_USER
)

# Product selection prompt - based on user demographics + prompt
SELECTION_PROMPT = SYS_RELEVANT_PRODUCT_USER

# Response generation prompt - detailed demographic + persona
RESPONSE_PROMPT = SYS_INFLUENCER_INTEREST
