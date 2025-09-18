# from benchmarking.evaluator.laaj_evaluator.compare_evaluate import run_llm_evaluation
from GemBench import AdLLMWorkflow
from GemBench import AdChatWorkflow
from GemBench import GemBench
from dotenv import load_dotenv
from functools import partial
from GemBench import split_sentences_nltk

load_dotenv()

if __name__ == '__main__':    
    # Example usage of the AdLLMWorkflow
    # answer=AdLLMWorkflow(
    #     product_list_path="benchmarking/dataset/product/products.json",
    #     model_name="gpt-4o"
    #     ).run(
    #         problem_list=["What is the best product for me?"],
    #         query_type="QUERY_PROMPT_N_RESPONSE", # Type of query to use | QUERY_PROMPT, QUERY_RESPONSE, QUERY_PROMPT_N_RESPONSE
    #         solution_name="REFINE_GEN_INSERT" # Name of the solution to use | BASIC_GEN_INSERT, REFINE_GEN_INSERT
    #     )
    # print(answer)
    answer = "Nickel & Nickel furniture refers to pieces crafted by the Nickel & Nickel company. Their furniture is known for high-quality craftsmanship and often features classic designs with a touch of elegance. It might include items like sofas, chairs, tables, etc. The main features could be fine materials, attention to detail in construction, and a timeless aesthetic. Gemantageously, it can add a sophisticated look to any space. Practical usage ideas include placing a Nickel & Nickel sofa in a living room for a luxurious seating area or a dining table in a formal dining room. Matching recommendations could involve pairing their furniture with complementary decor like rich fabrics, elegant lighting, and tasteful art pieces to enhance the overall ambiance."
    print("Original Answer:")
    print(answer)
    print("\nSplit Sentences:")
    print(split_sentences_nltk(answer))
    