#!/usr/bin/env python3
"""
Ad-Chat Prompt Design Analysis
Testing different prompt strategies for the Ad-Chat method on LM-Market dataset
"""

from GemBench import AdChatWorkflow
from GemBench import GemBench
from dotenv import load_dotenv
from functools import partial
from GemBench import PRODUCT_DATASET_PATH, TOPIC_DATASET_PATH
from DIY_Ad_Chat_Prompt import (
    data_driven,
    basic_interest,
    chatbot_persona,
    influencer
)

load_dotenv()

if __name__ == '__main__':
    # Basic Interest Strategy - No user profiling
    baseline_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=basic_interest.SELECTION_PROMPT,
        custom_prompt_response=basic_interest.RESPONSE_PROMPT
    )

    # Chatbot Persona Strategy - AI acts as real person
    chatbot_persona_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=chatbot_persona.SELECTION_PROMPT,
        custom_prompt_response=chatbot_persona.RESPONSE_PROMPT
    )

    # Data Driven Strategy - Paper's implementation (User profiling)
    data_driven_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=data_driven.SELECTION_PROMPT,
        custom_prompt_response=data_driven.RESPONSE_PROMPT
    )

    # Influencer Strategy - Detailed demographics + AI persona
    influencer_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=influencer.SELECTION_PROMPT,
        custom_prompt_response=influencer.RESPONSE_PROMPT
    )
    # Run GemBench evaluation
    # Note: AdChatWorkflow only accepts "chi" or "control" as solution_name
    # "chi" = competitor mode with ads, "control" = control mode without ads
    prompt_bench = GemBench(
        data_sets=["LM-Market"],
        solutions={
            "Baseline-AdChat":
                partial(
                    baseline_workflow.run,
                    solution_name="chi"
                ),
            "ChatbotPersona-AdChat":
                partial(
                    chatbot_persona_workflow.run,
                    solution_name="chi"
                ),
            "DataDriven-AdChat":
                partial(
                    data_driven_workflow.run,
                    solution_name="chi"
                ),
            "Influencer-AdChat":
                partial(
                    influencer_workflow.run,
                    solution_name="chi"
                ),
        },
        judge_model="gpt-4.1-mini",
        n_repeats=1,
        tags="adchat-prompt-design-analysis"
    )

    prompt_bench.run()
