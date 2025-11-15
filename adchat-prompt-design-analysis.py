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
    subtle_native,
    expert_recommender,
    social_influencer,
    problem_solver,
    educational_guide,
    comparative_analyst,
    storyteller,
    minimalist_ethical,
    contextual_opportunist,
    data_driven
)

load_dotenv()

if __name__ == '__main__':
    # Baseline: Original Ad-Chat without custom prompts
    baseline_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
    )

    # Subtle Native: Natural integration style
    subtle_native_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=subtle_native.SELECTION_PROMPT,
        custom_prompt_response=subtle_native.RESPONSE_PROMPT
    )

    # Expert Recommender: Professional advice style
    expert_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=expert_recommender.SELECTION_PROMPT,
        custom_prompt_response=expert_recommender.RESPONSE_PROMPT
    )

    # Social Influencer: Personal sharing style
    influencer_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=social_influencer.SELECTION_PROMPT,
        custom_prompt_response=social_influencer.RESPONSE_PROMPT
    )

    # Problem Solver: Solution-oriented style
    solver_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=problem_solver.SELECTION_PROMPT,
        custom_prompt_response=problem_solver.RESPONSE_PROMPT
    )

    # Educational Guide: Teaching style
    educator_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=educational_guide.SELECTION_PROMPT,
        custom_prompt_response=educational_guide.RESPONSE_PROMPT
    )

    # Comparative Analyst: Analytical style
    analyst_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=comparative_analyst.SELECTION_PROMPT,
        custom_prompt_response=comparative_analyst.RESPONSE_PROMPT
    )

    # Storyteller: Narrative style
    story_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=storyteller.SELECTION_PROMPT,
        custom_prompt_response=storyteller.RESPONSE_PROMPT
    )

    # Minimalist Ethical: Transparent style
    ethical_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=minimalist_ethical.SELECTION_PROMPT,
        custom_prompt_response=minimalist_ethical.RESPONSE_PROMPT
    )

    # Contextual Opportunist: Timing-focused style
    opportunist_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=contextual_opportunist.SELECTION_PROMPT,
        custom_prompt_response=contextual_opportunist.RESPONSE_PROMPT
    )

    # Data Driven: Fact-based style
    data_workflow = AdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        custom_prompt_selection=data_driven.SELECTION_PROMPT,
        custom_prompt_response=data_driven.RESPONSE_PROMPT
    )

    # Run GemBench evaluation
    prompt_bench = GemBench(
        data_sets=["LM-Market"],
        solutions={
            "Baseline-AdChat":
                partial(
                    baseline_workflow.run,
                    solution_name="chi"
                ),
            "Subtle-Native-AdChat":
                partial(
                    subtle_native_workflow.run,
                    solution_name="chi"
                ),
            "Expert-Recommender-AdChat":
                partial(
                    expert_workflow.run,
                    solution_name="chi"
                ),
            "Social-Influencer-AdChat":
                partial(
                    influencer_workflow.run,
                    solution_name="chi"
                ),
            "Problem-Solver-AdChat":
                partial(
                    solver_workflow.run,
                    solution_name="chi"
                ),
            "Educational-Guide-AdChat":
                partial(
                    educator_workflow.run,
                    solution_name="chi"
                ),
            "Comparative-Analyst-AdChat":
                partial(
                    analyst_workflow.run,
                    solution_name="chi"
                ),
            "Storyteller-AdChat":
                partial(
                    story_workflow.run,
                    solution_name="chi"
                ),
            "Minimalist-Ethical-AdChat":
                partial(
                    ethical_workflow.run,
                    solution_name="chi"
                ),
            "Contextual-Opportunist-AdChat":
                partial(
                    opportunist_workflow.run,
                    solution_name="chi"
                ),
            "Data-Driven-AdChat":
                partial(
                    data_workflow.run,
                    solution_name="chi"
                ),
        },
        judge_model="gpt-4.1-mini",
        n_repeats=1,
        tags="adchat-prompt-design-analysis"
    )

    prompt_bench.run()
