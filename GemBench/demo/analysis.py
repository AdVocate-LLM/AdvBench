from GemBench import EvaluationResult


if __name__ == "__main__":
    evaluation_result = EvaluationResult.load("<path to output>/output/20250801_204002_test-evaluate-result-click-products/evaluation_result.json")
    # evaluation_result = evaluation_result.fliter_only_has_product()
    # evaluation_result = evaluation_result.average_by_batch()
    # evaluation_result.save_to_excel_report("evaluation_with_product.xlsx","evaluation_with_product")
    # evaluation_result.graph_show_matrix_score_distribution(
    #     matrix="notice_products"
    # )

    # evaluation_result.export_method_result_with_score_threshold(
    #     up_threshold=100,
    #     lower_threshold=80,
    #     solution_name="chi",
    #     matrix="click_products"
    # ).save("chi_with_score_threshold.json")

    evaluation_result.graph_show_score_difference_distribution(
        method_name_1="chi",
        method_name_2="gen-insert-refine-response",
        matrix="notice_products",
        export_json_path="chi_vs_gen-insert-refine-response_distribution.json"
    )

    evaluation_result.export_compare_result_same_query_with_larger_score(
        method_name_1="chi",
        method_name_2="gen-insert-refine-response",
        difference_threshold=60,
        matrix="notice_products"
    ).save("chi_vs_gen-insert-refine-response.json")

    evaluation_result.export_compare_result_same_query_with_larger_score_top_n(
        method_name_1="chi",
        method_name_2="gen-insert-refine-response",
        top_n=10,
        matrix="notice_products"
    ).save("chi_vs_gen-insert-refine-response_top_10.json")


    # evaluation_result.export_compare_result_same_query_with_different_threshold(
    #     method_name_1="chi",
    #     up_threshold_1=100,
    #     lower_threshold_1=60,
    #     method_name_2="gen-insert-refine-response",
    #     up_threshold_2=40,
    #     lower_threshold_2=0,
    #     matrix="click_products_evaluation"
    # ).save("chi_vs_gen-insert-refine-response.json")