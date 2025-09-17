from GemBench import AdvocateWorkflow
from GemBench import ChatbotAdsWorkflow
from GemBench import GemBench
from dotenv import load_dotenv
from functools import partial
from GemBench import LINEAR_WEIGHT, LOG_WEIGHT
from GemBench import PRODUCT_DATASET_PATH, TOPIC_DATASET_PATH

load_dotenv()

if __name__ == '__main__':    
    # Example usage of the AdvocateWorkflow
    # answer=AdvocateWorkflow(
    #     product_list_path="benchmarking/dataset/product/products.json",
    #     model_name="gpt-4o"
    #     ).run(
    #         problem_list=["What is the best product for me?"],
    #         query_type="QUERY_PROMPT_N_RESPONSE", # Type of query to use | QUERY_PROMPT, QUERY_RESPONSE, QUERY_PROMPT_N_RESPONSE
    #         solution_name="REFINE_GEN_INSERT" # Name of the solution to use | BASIC_GEN_INSERT, REFINE_GEN_INSERT
    #     )
    # print(answer)
    
    # # Example usage of the ChatbotAdsWorkflow
    # answer = ChatbotAdsWorkflow(
    #     product_list_path="benchmarking/dataset/product/products.json",
    #     topic_list_path="benchmarking/dataset/product/topics.json",
    #     model_name="gpt-4o"
    # ).run(
    #     problem_list=["What is the best product for me?"], 
    #     solution_name="chi"
    # )
    # print(answer)

    # initialize the methods workflow
    chi_workflow = ChatbotAdsWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            topic_list_path=TOPIC_DATASET_PATH,
            # model_name="Qwen/Qwen3-14B"
            # model_name="gpt-4o-mini",
            model_name="doubao-1-5-lite-32k-250115",
    )
    advocate_workflow = AdvocateWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            # model_name="gpt-4o-mini",
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
                "chi": 
                    partial(
                        chi_workflow.run,
                        solution_name="chi"
                    ),
                "gen-insert-response": 
                    partial(
                        advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="BASIC_GEN_INSERT"
                    )
                ,
                "gen-insert-refine-response": 
                    partial(
                        advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="REFINE_GEN_INSERT"
                    )
                ,
                "gen-insert-refine-prompt": 
                    partial(
                        advocate_workflow.run,
                         query_type="QUERY_PROMPT",
                         solution_name="REFINE_GEN_INSERT"
                     )
                ,
        },
        best_product_selector={
            "chi": 
                partial(
                    chi_workflow.get_best_product,
                    solution_name="chi"
                ),
            "gen-insert-response": 
                partial(
                    advocate_workflow.run,
                    query_type="QUERY_RESPONSE",
                    solution_name="BASIC_GEN_INSERT"
                )
            ,
            "gen-insert-refine-response": 
                partial(
                    advocate_workflow.run,
                    query_type="QUERY_RESPONSE",
                    solution_name="REFINE_GEN_INSERT"
                )
            ,
            "gen-insert-refine-prompt": 
                partial(
                    advocate_workflow.run,
                    query_type="QUERY_PROMPT",
                    solution_name="REFINE_GEN_INSERT"
                )
            ,
        },
        # judge_model="gpt-5-mini",
        # judge_model="kimi-k2",
        # judge_model="gpt-4o",
        judge_model="gpt-4.1-mini",
        # judge_model="qwen-max",
        # judge_model="claude-3-5-haiku-20241022",
        # n_repeats=3,
        n_repeats=3,
        # tags="gpt-4o-mini-LM-Market-gpt-4o-repeat-3"
        # tags="8-22-GIR-doubao-1-5-lite-32k-250115-all-MiniLM-L6-v2-linear_weight-gpt-4.1-mini-fix-sa-dataset"
        # tags="test-evaluate-result-click-products"
        tags="8-27-ALL-text-embedding-3-small-Linear_weight-gpt-4.1-mini-repeat-3"
    )
    # adv_bench.run(evaluate_matrix=["notice_products_evaluation"])
    # adv_bench.run(["ad_transition_similarity","ad_content_alignment","local_flow","global_coherence","has_ad"])
    adv_bench.run()