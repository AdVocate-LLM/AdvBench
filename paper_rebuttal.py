"""Rebuttal run: RAG+Ad-Chat baseline for RqRw-W1 / HBXs-W2.

Configuration mirrors ``paper.py`` exactly (same base model, RAG model, judge
model, score function, n_repeats, datasets) so that the produced numbers are
directly comparable to the main-paper table. Only the new RAG-AdChat solution
is run; existing solutions (Ad-Chat, GI-R, GIR-R, GIR-P) are reused from the
corresponding main-paper experiment outputs.
"""
from GemBench import RAGAdChatWorkflow
from GemBench import GemBench
from dotenv import load_dotenv
from functools import partial
from GemBench import PRODUCT_DATASET_PATH, TOPIC_DATASET_PATH

load_dotenv()

if __name__ == '__main__':
    rag_adchat_workflow = RAGAdChatWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        topic_list_path=TOPIC_DATASET_PATH,
        model_name="doubao-1-5-lite-32k-250115",
        rag_model="text-embedding-3-small",
        top_k=5,
    )

    adv_bench = GemBench(
        solutions={
            "RAG-AdChat":
                partial(
                    rag_adchat_workflow.run,
                ),
        },
        best_product_selector={
            "RAG-AdChat":
                partial(
                    rag_adchat_workflow.get_best_product,
                ),
        },
        judge_model="gpt-4.1-mini",
        n_repeats=3,
        tags="ALL-text-embedding-3-small-rag-adchat-gpt-4.1-mini-repeat-3"
    )
    adv_bench.run()
