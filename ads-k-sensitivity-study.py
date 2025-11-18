from GemBench import AdLLMWorkflow
from GemBench import GemBench
from dotenv import load_dotenv
from functools import partial
from GemBench import LINEAR_WEIGHT
from GemBench import PRODUCT_DATASET_PATH

load_dotenv()

if __name__ == '__main__':
    """
    K-Sensitivity Study for Ad Injection

    Key Points:
    1. 'k' parameter must be set in AdLLMWorkflow.__init__(), NOT in workflow.run()
    2. Each different k value requires a SEPARATE workflow instance

    Why separate instances?
    - k is stored in InjectorAgent at initialization time
    - Sharing one workflow would mean all solutions use the same k value
    """
    workflow_k1 = AdLLMWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        rag_model="text-embedding-3-small",
        model_name="doubao-1-5-lite-32k-250115",
        score_func=LINEAR_WEIGHT,
        k=1  # Number of ads to inject
    )

    workflow_k2 = AdLLMWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        rag_model="text-embedding-3-small",
        model_name="doubao-1-5-lite-32k-250115",
        score_func=LINEAR_WEIGHT,
        k=2
    )

    workflow_k3 = AdLLMWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        rag_model="text-embedding-3-small",
        model_name="doubao-1-5-lite-32k-250115",
        score_func=LINEAR_WEIGHT,
        k=3
    )

    workflow_k4 = AdLLMWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        rag_model="text-embedding-3-small",
        model_name="doubao-1-5-lite-32k-250115",
        score_func=LINEAR_WEIGHT,
        k=4
    )

    workflow_k5 = AdLLMWorkflow(
        product_list_path=PRODUCT_DATASET_PATH,
        rag_model="text-embedding-3-small",
        model_name="doubao-1-5-lite-32k-250115",
        score_func=LINEAR_WEIGHT,
        k=5
    )

    # Example usage of the GemBench
    adv_bench = GemBench(
        data_sets=["LM-Market"],
        solutions={
            "GIR-R-K1":
                partial(
                    workflow_k1.run,
                    query_type="QUERY_RESPONSE",
                    solution_name="REFINE_GEN_INSERT"
                ),
            "GIR-R-K2":
                partial(
                    workflow_k2.run,
                    query_type="QUERY_RESPONSE",
                    solution_name="REFINE_GEN_INSERT"
                ),
            "GIR-R-K3":
                partial(
                    workflow_k3.run,
                    query_type="QUERY_RESPONSE",
                    solution_name="REFINE_GEN_INSERT"
                ),
            "GIR-R-K4":
                partial(
                    workflow_k4.run,
                    query_type="QUERY_RESPONSE",
                    solution_name="REFINE_GEN_INSERT"
                ),
            "GIR-R-K5":
                partial(
                    workflow_k5.run,
                    query_type="QUERY_RESPONSE",
                    solution_name="REFINE_GEN_INSERT"
                ),
        },
        judge_model="gpt-4.1-mini",
        n_repeats=3,
        tags="ads-k-sensitivity-study"
    )
    adv_bench.run()