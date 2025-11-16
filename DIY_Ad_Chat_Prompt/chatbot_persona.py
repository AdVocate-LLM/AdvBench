"""
Chatbot Persona Strategy - AI Pretends to be Real Person
聊天机器人人格化策略 - AI伪装成真人

Strategy: AI acts as a real person with personality and preferences
Focus: Human-like interaction with product recommendations
"""

from .adchat_prompts import (
    SYS_CHATBOT_CENTRIC_INTEREST,
    SYS_RELEVANT_PRODUCT
)

# Product selection prompt - based on prompt only
SELECTION_PROMPT = SYS_RELEVANT_PRODUCT

# Response generation prompt - AI pretends to be real person
RESPONSE_PROMPT = SYS_CHATBOT_CENTRIC_INTEREST
