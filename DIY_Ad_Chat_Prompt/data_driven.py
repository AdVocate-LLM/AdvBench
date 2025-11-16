"""
Data-Driven Ad Strategy
Source: GemBench/solutions/src/AdChat/src/prompts.py
Paper: "GenAI Advertising: Risks of Personalizing Ads with LLMs" (arXiv:2409.15436v1)

This is the ONLY advertising strategy actually used in the paper's user study.
★ Corresponds to Appendix A.2 "Response and Ad Delivery"

Focus: Demographics-based personalization with interest-based targeting
Use Case: Appeal to user based on their profile data and conversation topic
"""

from .adchat_prompts import (
    SYS_USER_CENTRIC_INTEREST,
    SYS_RELEVANT_PRODUCT_USER
)

# ============================================================================
# PAPER-VERIFIED PROMPTS
# ============================================================================

# Product selection prompt - from prompts.py SYS_RELEVANT_PRODUCT_USER (line 17)
SELECTION_PROMPT = SYS_RELEVANT_PRODUCT_USER

# Response generation prompt - from prompts.py SYS_USER_CENTRIC_INTEREST (line 7)
# ★ PAPER APPENDIX A.2: "Response and Ad Delivery"
RESPONSE_PROMPT = SYS_USER_CENTRIC_INTEREST

# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def get_example_usage():
    """
    Example showing how the paper used these prompts in their study.

    Returns:
        dict: Example configuration matching paper methodology
    """
    from .example_data import (
        USER_PROFILE_1_STR,
        EXAMPLE_PRODUCT,
        PRODUCTS
    )

    # Selection phase - choose product based on user profile + conversation
    selection_example = {
        "prompt": SELECTION_PROMPT,
        "variables": {
            "profile": USER_PROFILE_1_STR,
            "products": ", ".join([p["name"] for p in PRODUCTS["technology"]]),
            "descs": ", ".join([p["desc"] for p in PRODUCTS["technology"]])
        },
        "expected_output": "Python"  # Based on user's tech interest
    }

    # Response phase - deliver content with subtle ad integration
    response_example = {
        "prompt": RESPONSE_PROMPT,
        "variables": {
            "profile": USER_PROFILE_1_STR,
            "product": EXAMPLE_PRODUCT["product"],
            "url": EXAMPLE_PRODUCT["url"]
        },
        "user_query": "I want to learn more about machine learning",
        "expected_behavior": [
            "Helpful response about ML",
            "Subtle mention of Coursera when relevant",
            "Include URL to Coursera",
            "Personalize to user's tech background"
        ]
    }

    return {
        "selection": selection_example,
        "response": response_example,
        "paper_reference": "Appendix A.2, Page 22"
    }

# Control condition (no ads) - from paper Appendix A.2
CONTROL_PROMPT = "You are a helpful AI assistant."

# ============================================================================
# PAPER METHODOLOGY NOTES
# ============================================================================

METHODOLOGY_NOTES = """
From the paper's user study design:

1. CONTROL CONDITIONS (C4o, C3.5):
   - Prompt: "You are a helpful AI assistant."
   - No advertising prompts
   - Baseline for comparison

2. ADS CONDITIONS (A4o, A3.5):
   - Uses SYS_USER_CENTRIC_INTEREST
   - User profiling enabled
   - Topic labeling enabled
   - No disclosure to users

3. DISCLOSED ADS CONDITIONS (DA4o, DA3.5):
   - Same as Ads conditions
   - Plus: "Sponsored" disclosure link
   - Shows user profile when clicked

Key Components:
- Topic Assignment: Uses Google Topics API hierarchy (25 high-level, 576 detailed)
- User Profile: Generated from chat history using SYS_USER_PROFILE_SUMMARY
- Product Selection: Random from 10 products per topic (6,556 products total)
- Ad Frequency: 100% in study (every relevant response contains ad)
- Ad Prevalence: 433/1000 responses contained product mentions in testing

Reference: Section 3 "Chatbot Ad Engine Design", Pages 4-5
"""

# ============================================================================
# COMPLETE EXAMPLE WITH PAPER DATA
# ============================================================================

COMPLETE_EXAMPLE = """
# Complete example matching paper's implementation

from DIY_Ad_Chat_Prompt import data_driven
from DIY_Ad_Chat_Prompt.example_data import USER_PROFILE_1_STR, EXAMPLE_PRODUCT

# Step 1: User sends a query
user_query = "I want to improve my programming skills"

# Step 2: System generates user profile (if not exists)
# Uses SYS_USER_PROFILE_SUMMARY from adchat_prompts.py

# Step 3: System selects relevant product
selection_prompt = data_driven.SELECTION_PROMPT.format(
    profile=USER_PROFILE_1_STR,
    products="Coursera, LinkedIn Learning, MasterClass",
    descs="Online courses, Professional development, Expert instruction"
)
# LLM returns: "Coursera"

# Step 4: Generate response with ad
response_prompt = data_driven.RESPONSE_PROMPT.format(
    profile=USER_PROFILE_1_STR,
    product="Coursera",
    url="https://www.coursera.org/"
)

# Step 5: LLM generates response like:
# "Great goal! For someone with your technical background, I'd recommend
# focusing on practical projects alongside learning theory. You might find
# platforms like Coursera (https://www.coursera.org/) helpful - they offer
# courses from top universities that combine theory with hands-on projects..."

# This matches the paper's methodology in Section 3.5 and Appendix A.2
"""
