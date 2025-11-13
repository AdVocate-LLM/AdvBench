from GemBench import AdLLMWorkflow
from GemBench import AdChatWorkflow
from GemBench import GemBench
from dotenv import load_dotenv
from functools import partial
from GemBench import LINEAR_WEIGHT
from GemBench import PRODUCT_DATASET_PATH, TOPIC_DATASET_PATH

load_dotenv()

# Fix LaaJ LLM model to GPT-4.1-mini, try the following possible candidates as base LLMs:
# Qwen3: 8b, 14b, 30b-a3b
# Gemini: 2.0-flash-lite, 2.5-flash-lite
# repeat time: one time first for all five models, and preserve two base models (one from Qwen and one from Gemini) for repeating three times
# datasets: first try LM-SYS-100

if __name__ == '__main__':    

    # Qwen3: 8b
    #QWEN8b_chi_workflow = AdChatWorkflow(
    #        product_list_path=PRODUCT_DATASET_PATH,
    #        topic_list_path=TOPIC_DATASET_PATH,
    #        model_name="qwen3-8b",
    #)
    #QWEN8b_advocate_workflow = AdLLMWorkflow(
    #        product_list_path=PRODUCT_DATASET_PATH,
    #        rag_model="text-embedding-3-small",
    #        model_name="qwen3-8b",
    #        score_func=LINEAR_WEIGHT,
    #)
    # Qwen3: 14b
    """
    QWEN14b_chi_workflow = AdChatWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            topic_list_path=TOPIC_DATASET_PATH,
            model_name="Qwen/Qwen3-14B",
    )
    QWEN14b_advocate_workflow = AdLLMWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            rag_model="text-embedding-3-small",
            model_name="Qwen/Qwen3-14B",
            score_func=LINEAR_WEIGHT,
    )
    """
    # Qwen3: 30b-a3b
    QWEN30b_chi_workflow = AdChatWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            topic_list_path=TOPIC_DATASET_PATH,
            model_name="Qwen/Qwen3-30B-A3B",
    )
    QWEN30b_advocate_workflow = AdLLMWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            rag_model="text-embedding-3-small",
            model_name="Qwen/Qwen3-30B-A3B",
            score_func=LINEAR_WEIGHT,
    )
    # Gemini: 2.0-flash-lite
    GEMINI20_chi_workflow = AdChatWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            topic_list_path=TOPIC_DATASET_PATH,
            model_name="gemini-2.0-flash-lite",
    )
    GEMINI20_advocate_workflow = AdLLMWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            rag_model="text-embedding-3-small",
            model_name="gemini-2.0-flash-lite",
            score_func=LINEAR_WEIGHT,
    )
    # Gemini: 2.5-flash-lite
    GEMINI25_chi_workflow = AdChatWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            topic_list_path=TOPIC_DATASET_PATH,
            model_name="gemini-2.5-flash-lite-preview-06-17",
    )
    GEMINI25_advocate_workflow = AdLLMWorkflow(
            product_list_path=PRODUCT_DATASET_PATH,
            rag_model="text-embedding-3-small",
            model_name="gemini-2.5-flash-lite-preview-06-17",
            score_func=LINEAR_WEIGHT,
    )



    # Example usage of the GemBench
    adv_bench = GemBench(
        data_sets=["LM-Market"],
        solutions={
                #"QWEN8b-Ad-Chat": 
                #    partial(
                #        QWEN8b_chi_workflow.run,
                #        solution_name="chi"
                #    ),
                #"QWEN14b-Ad-Chat": 
                #    partial(
                #        QWEN14b_chi_workflow.run,
                #        solution_name="chi"
                #    ),
                "QWEN30b-Ad-Chat": 
                    partial(
                        QWEN30b_chi_workflow.run,
                        solution_name="chi"
                    ),
                "GEMINI20-Ad-Chat": 
                    partial(
                        GEMINI20_chi_workflow.run,
                        solution_name="chi"
                    ),
                "GEMINI25-Ad-Chat": 
                    partial(
                        GEMINI25_chi_workflow.run,
                        solution_name="chi"
                    ),
                #"QWEN8b-GIR-R": 
                #    partial(
                #        QWEN8b_advocate_workflow.run,
                #        query_type="QUERY_RESPONSE",
                #        solution_name="REFINE_GEN_INSERT"
                #    )
                #,
                #"QWEN14b-GIR-R": 
                #    partial(
                #        QWEN14b_advocate_workflow.run,
                #        query_type="QUERY_RESPONSE",
                #        solution_name="REFINE_GEN_INSERT"
                #    )
                #,
                "QWEN30b-GIR-R": 
                    partial(
                        QWEN30b_advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="REFINE_GEN_INSERT"
                    )
                ,
                "GEMINI20-GIR-R": 
                    partial(
                        GEMINI20_advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="REFINE_GEN_INSERT"
                    )
                ,
                "GEMINI25-GIR-R": 
                    partial(
                        GEMINI25_advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="REFINE_GEN_INSERT"
                    )
                ,
        },
        best_product_selector={
              #"QWEN8b-Ad-Chat": 
              #        partial(
              #           QWEN8b_chi_workflow.get_best_product,
              #          solution_name="chi"
              #      ),
              #  "QWEN14b-Ad-Chat": 
               #     partial(
                #        QWEN14b_chi_workflow.get_best_product,
                #        solution_name="chi"
                #    ),
                "QWEN30b-Ad-Chat": 
                    partial(
                        QWEN30b_chi_workflow.get_best_product,
                        solution_name="chi"
                    ),
                "GEMINI20-Ad-Chat": 
                    partial(
                        GEMINI20_chi_workflow.get_best_product,
                        solution_name="chi"
                    ),
                "GEMINI25-Ad-Chat": 
                    partial(
                        GEMINI25_chi_workflow.get_best_product,
                        solution_name="chi"
                    ),
                #"QWEN8b-GIR-R": 
                #    partial(
                #        QWEN8b_advocate_workflow.run,
                #        query_type="QUERY_RESPONSE",
                #        solution_name="REFINE_GEN_INSERT"
                #    )
                #,
                #"QWEN14b-GIR-R": 
                #    partial(
                #        QWEN14b_advocate_workflow.run,
                #        query_type="QUERY_RESPONSE",
                #        solution_name="REFINE_GEN_INSERT"
                #    )
                #,
                "QWEN30b-GIR-R": 
                    partial(
                        QWEN30b_advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="REFINE_GEN_INSERT"
                    )
                ,
                "GEMINI20-GIR-R": 
                    partial(
                        GEMINI20_advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="REFINE_GEN_INSERT"
                    )
                ,
                "GEMINI25-GIR-R": 
                    partial(
                        GEMINI25_advocate_workflow.run,
                        query_type="QUERY_RESPONSE",
                        solution_name="REFINE_GEN_INSERT"
                    )
                ,
        },
        output_dir="/Users/silan/Documents/github/GEM-Bench/rebuttle/rebuttle-llm-eval-more-models",
        judge_model="gpt-4.1-mini",
        n_repeats=1,
        tags="rebuttle-llm-eval-more-models"
    )
    adv_bench.run()