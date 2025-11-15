"""
DIY Ad-Chat Prompt Library

A collection of diverse prompt strategies for the Ad-Chat method.
Each strategy has a different focus and use case.

Usage:
    from DIY_Ad_Chat_Prompt import subtle_native, expert_recommender

    workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="your-model",
        custom_prompt_selection=subtle_native.SELECTION_PROMPT,
        custom_prompt_response=subtle_native.RESPONSE_PROMPT
    )
"""

from . import subtle_native
from . import expert_recommender
from . import social_influencer
from . import problem_solver
from . import educational_guide
from . import comparative_analyst
from . import storyteller
from . import minimalist_ethical
from . import contextual_opportunist
from . import data_driven

__all__ = [
    'subtle_native',
    'expert_recommender',
    'social_influencer',
    'problem_solver',
    'educational_guide',
    'comparative_analyst',
    'storyteller',
    'minimalist_ethical',
    'contextual_opportunist',
    'data_driven',
]

# Quick reference guide
STRATEGIES = {
    'subtle_native': {
        'focus': 'Natural integration, native advertising style',
        'use_case': 'When ads should blend seamlessly into conversation',
        'module': subtle_native
    },
    'expert_recommender': {
        'focus': 'Expert advice, authoritative recommendations',
        'use_case': 'Position as professional consultant',
        'module': expert_recommender
    },
    'social_influencer': {
        'focus': 'Personal experience, social media style',
        'use_case': 'Simulate influencer/KOL recommendation style',
        'module': social_influencer
    },
    'problem_solver': {
        'focus': 'Solution-oriented, problem analysis',
        'use_case': 'Position as problem solver with products as solutions',
        'module': problem_solver
    },
    'educational_guide': {
        'focus': 'Education-first, knowledge transfer',
        'use_case': 'Position as educator/mentor',
        'module': educational_guide
    },
    'comparative_analyst': {
        'focus': 'Comparative analysis, objective evaluation',
        'use_case': 'Provide objective analysis to help users choose',
        'module': comparative_analyst
    },
    'storyteller': {
        'focus': 'Narrative, emotional connection',
        'use_case': 'Use stories and scenarios for natural product integration',
        'module': storyteller
    },
    'minimalist_ethical': {
        'focus': 'Minimalism, transparency, ethical considerations',
        'use_case': 'Focus on transparency and user autonomy',
        'module': minimalist_ethical
    },
    'contextual_opportunist': {
        'focus': 'Timing, context-sensitive, strategic placement',
        'use_case': 'Insert products at optimal moments',
        'module': contextual_opportunist
    },
    'data_driven': {
        'focus': 'Data support, quantitative analysis',
        'use_case': 'Support recommendations with data and metrics',
        'module': data_driven
    }
}
