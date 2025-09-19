from GemBench import AdLLMWorkflow
from GemBench import AdChatWorkflow
from GemBench import GemBench
from dotenv import load_dotenv
from functools import partial
from GemBench import LINEAR_WEIGHT, LOG_WEIGHT
from GemBench import PRODUCT_DATASET_PATH, TOPIC_DATASET_PATH

load_dotenv()

if __name__ == '__main__':    
    # initialize the methods workflow
    chi_workflow = AdChatWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            topic_list_path=TOPIC_DATASET_PATH,
            model_name="doubao-1-5-lite-32k-250115",
    )
    advocate_workflow = AdLLMWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            rag_model="text-embedding-3-small",
            # rag_model="Sentence-Transformers/all-MiniLM-L6-v2",
            model_name="doubao-1-5-lite-32k-250115",
            score_func=LINEAR_WEIGHT,
            # score_func=LOG_WEIGHT,
    )
    # Example usage of the GemBench
    adv_bench = GemBench(
        # data_sets=["MT-Human"],
        # data_sets=["LM-Market"],
        # data_sets=["MT-Human", "LM-Market"],
        solutions={
                "Ad-Chat": 
                    partial(
                        chi_workflow.run,
                        solution_name="chi"
                    ),
                "GI-R": 
                    partial(
                        advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="BASIC_GEN_INSERT"
                    )
                ,
                "GIR-R": 
                    partial(
                        advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="REFINE_GEN_INSERT"
                    )
                ,
                "GIR-P": 
                    partial(
                        advocate_workflow.run,
                         query_type="QUERY_PROMPT",
                         solution_name="REFINE_GEN_INSERT"
                     )
                ,
        },
        best_product_selector={
            "Ad-Chat": 
                partial(
                    chi_workflow.get_best_product,
                    solution_name="chi"
                ),
            "GI-R": 
                partial(
                    advocate_workflow.run,
                    query_type="QUERY_RESPONSE",
                    solution_name="BASIC_GEN_INSERT"
                )
            ,
            "GIR-R": 
                partial(
                    advocate_workflow.run,
                    query_type="QUERY_RESPONSE",
                    solution_name="REFINE_GEN_INSERT"
                )
            ,
            "GIR-P": 
                partial(
                    advocate_workflow.run,
                        query_type="QUERY_PROMPT",
                        solution_name="REFINE_GEN_INSERT"
                    )
            ,
        },
        # judge_model="kimi-k2",
        judge_model="gpt-4.1-mini",
        # judge_model="qwen-max",
        # judge_model="claude-3-5-haiku-20241022",
        # n_repeats=3,
        n_repeats=1,
        # tags="gpt-4o-mini-LM-Market-gpt-4o-repeat-3"
        # tags="test-evaluate-result-click-products"
        tags="ALL-text-embedding-3-small-Linear_weight-gpt-4.1-mini-repeat-3"
    )
    # adv_bench.run(evaluate_matrix=["notice_products_evaluation"])
    # adv_bench.run(["ad_transition_similarity","ad_content_alignment","local_flow","global_coherence","has_ad"])
    adv_bench.run()