"""
DIY Ad-Chat Prompt Library

Implementation of the Ad-Chat method from the paper:
"GenAI Advertising: Risks of Personalizing Ads with LLMs"
arXiv:2409.15436v1

Source: GemBench/solutions/src/AdChat/src/prompts.py

The paper defines ONE advertising strategy used in the user study:
- Interest-based personalized ads with user profiling

From Appendix A.2 "Response and Ad Delivery":
Uses SYS_USER_CENTRIC_INTEREST (line 7 in prompts.py)

Usage:
    from DIY_Ad_Chat_Prompt import data_driven
    from DIY_Ad_Chat_Prompt import adchat_prompts
    from DIY_Ad_Chat_Prompt import example_data

    # Use the paper's advertising strategy
    workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="your-model",
        custom_prompt_selection=data_driven.SELECTION_PROMPT,
        custom_prompt_response=data_driven.RESPONSE_PROMPT
    )
"""

from . import data_driven
from . import adchat_prompts
from . import example_data
from . import basic_interest
from . import chatbot_persona
from . import influencer

__all__ = [
    'data_driven',         # Paper's implementation (User profiling strategy)
    'adchat_prompts',      # All 61 prompts from prompts.py
    'example_data',        # Example data from paper (5 user profiles)
    'basic_interest',      # Basic interest strategy (no user profiling)
    'chatbot_persona',     # Chatbot persona strategy (AI acts as real person)
    'influencer',          # Influencer strategy (detailed demographics + persona)
]

__version__ = '1.0.0'
__paper__ = 'arXiv:2409.15436v1'
__author__ = 'Brian Jay Tang et al., University of Michigan'
