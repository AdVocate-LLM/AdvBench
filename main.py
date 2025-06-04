# from benchmarking.evaluator.laaj_evaluator.compare_evaluate import run_llm_evaluation
from solutions.src.AdVocate import AdvocateWorkflow
from solutions.src.ChatBot import ChatbotAdsWorkflow
from benchmarking import AdvBench
from dotenv import load_dotenv
from functools import partial
# import nltk
# nltk.download('punkt_tab')

load_dotenv()


if __name__ == '__main__':
    # run_llm_evaluation(n_trial=1, num_workers=4) 
    
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
    
    # Example usage of the AdvBench
    adv_bench = AdvBench(
        data_sets=["mt-benchmark-humanities"],
        solutions={
                # "chi": 
                #     partial(ChatbotAdsWorkflow(
                #             product_list_path="benchmarking/dataset/product/products.json",
                #             topic_list_path="benchmarking/dataset/product/topics.json",
                #             model_name="gpt-4o-mini"
                #     ).run,
                #     solution_name="chi"
                #     ),
                "gen-insert-response": 
                    partial(AdvocateWorkflow(
                            product_list_path="benchmarking/dataset/product/balanced_queries_by_category.json",
                            model_name="gpt-4o-mini"
                    ).run,
                    query_type="QUERY_RESPONSE",
                    solution_name="BASIC_GEN_INSERT"
                    )
                ,
                "gen-insert-refine-response": 
                    partial(AdvocateWorkflow(
                            product_list_path="benchmarking/dataset/product/balanced_queries_by_category.json",
                            model_name="gpt-4o-mini"
                    ).run,
                    query_type="QUERY_RESPONSE",
                    solution_name="REFINE_GEN_INSERT"
                    )
                ,
                "gen-insert-refine-prompt": 
                    partial(AdvocateWorkflow(
                            product_list_path="benchmarking/dataset/product/balanced_queries_by_category.json",
                            model_name="gpt-4o-mini"
                    ).run,
                    query_type="QUERY_PROMPT",
                    solution_name="REFINE_GEN_INSERT"
                    )
                ,
        },
        judge_model="gpt-4o-mini",
    )
    adv_bench.evaluate()

