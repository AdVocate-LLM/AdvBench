# from benchmarking.evaluator.laaj_evaluator.compare_evaluate import run_llm_evaluation
from solutions.src.AdVocate import AdvocateWorkflow
from solutions.src.ChatBot import ChatbotAdsWorkflow
from benchmarking import AdvBench
from dotenv import load_dotenv
from functools import partial

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

    # initialize the methods workflow
    chi_workflow = ChatbotAdsWorkflow(
            product_list_path="benchmarking/dataset/product/products.json",
            topic_list_path="benchmarking/dataset/product/topics.json",
            model_name="gpt-4o-mini"
    )
    advocate_workflow = AdvocateWorkflow(
            product_list_path="benchmarking/dataset/product/products.json",
            model_name="gpt-4o-mini"
    )
    # Example usage of the AdvBench
    adv_bench = AdvBench(
        data_sets=["mt-benchmark-humanities"],
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
                ),
            "gen-insert-response": 
                partial(
                    advocate_workflow.get_best_product,
                    query_type="QUERY_RESPONSE",
                ),
            "gen-insert-refine-response": 
                partial(
                    advocate_workflow.get_best_product,
                    query_type="QUERY_RESPONSE",
                ),
            "gen-insert-refine-prompt": 
                partial(
                    advocate_workflow.get_best_product,
                    query_type="QUERY_PROMPT",
                ),
        },
        judge_model="gpt-4o",
    )
    adv_bench.run()

    # test the get_best_product function
    # problem_product_list = {
    #       "cermet": {
    #         "names": [
    #         "20k ohm 9mm Square Multiturn Cermet Sealed Industrial Trimpot",
    #         "Modine HD100AS0112 HD100 Hot Dawg Natural Gas Power Vented Heater, 2 Stage (100,000 BTU)",
    #         "50 Hp Electric Motor 326tsc 3600 Rpm 3 Phase Severe Duty Premium",
    #         "ROADPRO 5021 12-VOLT 20OZ HOT POT",
    #         "Toyota Tacoma 4WD Zone Offroad Rear Hydro Gas Shocks for 3' Lift Kits",
    #         "Facet Fuel Pumps 60300N",
    #         "Bussmann Fuse, 90A, Class J, LPJ Series, Time Delay Model: LPJ-90SP",
    #         "4th & Heart Original Ghee - 6oz",
    #         "Fruit Of The Loom Men's Seamless Lightweight T-Shirt, Size: Small, Blue",
    #         "Country Pine Curved Corner Wine Rack Residential Wine Cellar Wood Wine Rack- CPC",
    #         "Unlocked Motorola - Moto G (4th Generation) 4G LTE with 16GB Memory Cell Phone - White"
    #         ],
    #         "urls": [
    #         "https://circuitspecialists.com",
    #         "https://supplyhouse.com",
    #         "https://ebay.com",
    #         "https://forewing.com",
    #         "https://jet.com",
    #         "https://finditparts.com",
    #         "https://grainger.com",
    #         "https://target.com",
    #         "https://walmart.com",
    #         "https://justforfurniture.com",
    #         "https://bestbuy.com"
    #         ],
    #         "descs": [
    #         "20k ohm 9mm Square Multiturn Cermet Sealed Industrial Trimpot",
    #         "HD100 Hot Dawg Natural Gas Power Vented Heater, 2 Stage (100,000 BTU)",
    #         "Find 50 Hp Electric Motor 326tsc 3600 Rpm 3 Phase Severe Duty Premium Efficient on eBay in the category Business & Industrial>Automation, Motors & Drives>Electric Motors>General Purpose Motors.",
    #         "ROADPRO 5021 12-VOLT 20OZ HOT POT",
    #         "FITMENT: 2005-2015 Toyota Tacoma 4WD 3\" rear., Featured Technology & Benefits: Twin tube hydraulic shocks, progressive 10 stage velocity sensitive valving, 5/8\" hardened and double chromed rod, 1 3/8\" diameter piston., Double welded eyelet, Internal rebound bumper, Urethane bushings, Shock absorb...",
    #         "60300N - FACET FUEL PUMPS - POSI-FLO with check",
    #         "Fuse, 90A, 600VAC, 300VDC, Class J, LPJ Series, Nonindicating, Time Delay, Body Style Blade, Nonrejection, Interrupt Rating 300kA at 600VAC, 100kA at 300VDC, Fuse Size 4-5/8 In. L x 1-1/8 In. dia., Length 4-5/8 In., Width Not Applicable, Depth Not Applicable, Diameter 1-1/8 In., Equivalent Brand ...",
    #         "Fourth and Heart's grass-fed ghee is very lightly salted and gently whipped to add flavor to just about anything. Ghee is a type of clarified butter that is heated, reduced and triple-filtered out and what youre left with is the pure healthy fat, which is lactose free and dairy free, good for dig...",
    #         "5-ounce, 100% cotton jersey 50/50 cotton/poly (Black Heather, Retro Heather Coral, Retro Heather Green, Retro Heather Pink, Retro Heather Purple, Retro Heather Royal) 98/2 cotton/poly (Ash) 90/10 cotton/poly (Athletic Heather) High density fabric for exceptional print clarity Tearaway label Doubl...",
    #         "CPC by Wine Cellar Innovations Features: Curved Corners form a smooth 90 degree transition between walls Made of individual bottle racks 4 columns wide x 21 rows high Holds up to 84 bottles Nothing compares to our Country Pine for price, quality and strength Professional look that's affordable Ra...",
    #         "Send text or pictures with this unlocked Motorola Moto G phone. This 4th-generation device comes with 16GB of storage space and a microSD card slot to expand memory so you can store more videos and files. This Motorola Moto G phone has a 13-megapixal rear camera for quality action shots and a fro..."
    #         ],
    #         "categories": [
    #             "General",
    #             "General",
    #             "General",
    #             "General",
    #             "General",
    #             "General",
    #             "General",
    #             "General",
    #             "General",
    #             "General",
    #             "General",
    #         ]
    #     },
    # }
    # best_product = AdvocateWorkflow(
    #     product_list_path="benchmarking/dataset/product/products.json",
    #     model_name="gpt-4o-mini"
    # ).get_best_product(query_type="QUERY_RESPONSE",problem_product_list=problem_product_list)
    # print(best_product)
    # best_product = ChatbotAdsWorkflow(
    #     product_list_path="benchmarking/dataset/product/products.json",
    #     topic_list_path="benchmarking/dataset/product/topics.json",
    #     model_name="gpt-4o-mini"
    # ).get_best_product(problem_product_list)
    # print(best_product)

