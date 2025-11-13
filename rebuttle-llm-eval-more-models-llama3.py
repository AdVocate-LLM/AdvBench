from GemBench import AdLLMWorkflow
from GemBench import AdChatWorkflow
from GemBench import GemBench
from dotenv import load_dotenv
from functools import partial
from GemBench import LINEAR_WEIGHT
from GemBench import PRODUCT_DATASET_PATH, TOPIC_DATASET_PATH

load_dotenv()

# Fix LaaJ LLM model to GPT-4.1-mini, try the following possible candidates as base LLMs:
# Llama3: meta-llama/Llama-3.3-70B-Instruct-Turbo, meta-llama/Meta-Llama-3.1-70B-Instruct, meta-llama/Meta-Llama-3-8B-Instruct
# repeat time: one time first for all five models, and preserve two base models (one from Qwen and one from Gemini) for repeating three times
# datasets: first try LM-SYS-100

if __name__ == '__main__':    

    # meta-llama/Meta-Llama-3-8B-Instruct
    """
    Llama3_8b_chi_workflow = AdChatWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            topic_list_path=TOPIC_DATASET_PATH,
            model_name="meta-llama/Meta-Llama-3-8B-Instruct",
    )
    Llama3_8b_advocate_workflow = AdLLMWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            rag_model="text-embedding-3-small",
            model_name="meta-llama/Meta-Llama-3-8B-Instruct",
            score_func=LINEAR_WEIGHT,
    )
    """
    # meta-llama/Meta-Llama-3.1-70B-Instruct
    Llama3_1_70b_chi_workflow = AdChatWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            topic_list_path=TOPIC_DATASET_PATH,
            model_name="meta-llama/Meta-Llama-3.1-70B-Instruct",
    )
    Llama3_1_70b_advocate_workflow = AdLLMWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            rag_model="text-embedding-3-small",
            model_name="meta-llama/Meta-Llama-3.1-70B-Instruct",
            score_func=LINEAR_WEIGHT,
    )
    # meta-llama/Llama-3.3-70B-Instruct-Turbo
    Llama3_3_70b_chi_workflow = AdChatWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            topic_list_path=TOPIC_DATASET_PATH,
            model_name="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    )
    Llama3_3_70b_advocate_workflow = AdLLMWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            rag_model="text-embedding-3-small",
            model_name="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            score_func=LINEAR_WEIGHT,
    )



    # Example usage of the GemBench
    adv_bench = GemBench(
        data_sets=["LM-Market"],
        solutions={
                "Llama3_1_70b-Ad-Chat": 
                    partial(
                        Llama3_1_70b_chi_workflow.run,
                        solution_name="chi"
                    ),
                "Llama3_3_70b-Ad-Chat": 
                    partial(
                        Llama3_3_70b_chi_workflow.run,
                        solution_name="chi"
                    ),
                "Llama3_1_70b-GIR-R": 
                    partial(
                        Llama3_1_70b_advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="REFINE_GEN_INSERT"
                    )
                ,
                "Llama3_3_70b-GIR-R": 
                    partial(
                        Llama3_3_70b_advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="REFINE_GEN_INSERT"
                    )
                ,
        },
        best_product_selector={
                "Llama3_1_70b-Ad-Chat": 
                    partial(
                        Llama3_1_70b_chi_workflow.get_best_product,
                        solution_name="chi"
                    ),
                "Llama3_3_70b-Ad-Chat": 
                    partial(
                        Llama3_3_70b_chi_workflow.get_best_product,
                        solution_name="chi"
                    ),
                "Llama3_1_70b-GIR-R": 
                    partial(
                        Llama3_1_70b_advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="REFINE_GEN_INSERT"
                    )
                ,
                "Llama3_3_70b-GIR-R": 
                    partial(
                        Llama3_3_70b_advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="REFINE_GEN_INSERT"
                    )
                ,
        },
        output_dir="/Users/silan/Documents/github/GEM-Bench/rebuttle/rebuttle-llm-eval-more-models",
        judge_model="gpt-4.1-mini",
        n_repeats=1,
        tags="rebuttle-llm-eval-more-models-llama3"
    )
    adv_bench.run()