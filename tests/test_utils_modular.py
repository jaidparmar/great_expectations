def candidate_test_is_on_temporary_notimplemented_list_cfe(context, expectation_type):
    if context in ["sqlite", "postgresql", "mysql", "mssql"]:
        return expectation_type in [
            "expect_select_column_values_to_be_unique_within_record",
            # "expect_table_columns_to_match_set",
            "expect_table_column_count_to_be_between",
            "expect_table_column_count_to_equal",
            # "expect_column_to_exist",
            # "expect_table_columns_to_match_ordered_list",
            # "expect_table_row_count_to_be_between",
            # "expect_table_row_count_to_equal",
            "expect_table_row_count_to_equal_other_table",
            # "expect_column_values_to_be_unique",
            # "expect_column_values_to_not_be_null",
            # "expect_column_values_to_be_null",
            "expect_column_values_to_be_of_type",
            "expect_column_values_to_be_in_type_list",
            # "expect_column_values_to_be_in_set",
            # "expect_column_values_to_not_be_in_set",
            # "expect_column_values_to_be_between",
            "expect_column_values_to_be_increasing",
            "expect_column_values_to_be_decreasing",
            # "expect_column_value_lengths_to_be_between",
            # "expect_column_value_lengths_to_equal",
            # "expect_column_values_to_match_regex",
            # "expect_column_values_to_not_match_regex",
            # "expect_column_values_to_match_regex_list",
            # "expect_column_values_to_not_match_regex_list",
            # "expect_column_values_to_match_like_pattern",
            # "expect_column_values_to_not_match_like_pattern",
            # "expect_column_values_to_match_like_pattern_list",
            # "expect_column_values_to_not_match_like_pattern_list",
            "expect_column_values_to_match_strftime_format",
            "expect_column_values_to_be_dateutil_parseable",
            "expect_column_values_to_be_json_parseable",
            "expect_column_values_to_match_json_schema",
            "expect_column_distinct_values_to_be_in_set",
            # "expect_column_distinct_values_to_contain_set",
            # "expect_column_distinct_values_to_equal_set",
            # "expect_column_mean_to_be_between",
            # "expect_column_median_to_be_between",
            "expect_column_quantile_values_to_be_between",
            "expect_column_stdev_to_be_between",
            # "expect_column_unique_value_count_to_be_between",
            # "expect_column_proportion_of_unique_values_to_be_between",
            "expect_column_most_common_value_to_be_in_set",
            # "expect_column_max_to_be_between",
            # "expect_column_min_to_be_between",
            # "expect_column_sum_to_be_between",
            "expect_column_pair_values_A_to_be_greater_than_B",
            "expect_column_pair_values_to_be_equal",
            "expect_column_pair_values_to_be_in_set",
            "expect_multicolumn_values_to_be_unique",
            "expect_multicolumn_sum_to_equal",
            "expect_column_pair_cramers_phi_value_to_be_less_than",
            # "expect_column_kl_divergence_to_be_less_than",
            "expect_column_bootstrapped_ks_test_p_value_to_be_greater_than",
            "expect_column_chisquare_test_p_value_to_be_greater_than",
            "expect_column_parameterized_distribution_ks_test_p_value_to_be_greater_than",
            "expect_compound_columns_to_be_unique",
        ]
    if context == "spark":
        return expectation_type in [
            "expect_select_column_values_to_be_unique_within_record",
            # "expect_table_columns_to_match_set",
            "expect_table_column_count_to_be_between",
            "expect_table_column_count_to_equal",
            # "expect_column_to_exist",
            # "expect_table_columns_to_match_ordered_list",
            # "expect_table_row_count_to_be_between",
            # "expect_table_row_count_to_equal",
            "expect_table_row_count_to_equal_other_table",
            # "expect_column_values_to_be_unique",
            # "expect_column_values_to_not_be_null",
            # "expect_column_values_to_be_null",
            "expect_column_values_to_be_of_type",
            "expect_column_values_to_be_in_type_list",
            "expect_column_values_to_be_in_set",
            "expect_column_values_to_not_be_in_set",
            # "expect_column_values_to_be_between",
            # "expect_column_values_to_be_increasing",
            # "expect_column_values_to_be_decreasing",
            # "expect_column_value_lengths_to_be_between",
            # "expect_column_value_lengths_to_equal",
            # "expect_column_values_to_match_regex",
            # "expect_column_values_to_not_match_regex",
            # "expect_column_values_to_match_regex_list",
            "expect_column_values_to_not_match_regex_list",
            "expect_column_values_to_match_like_pattern",
            "expect_column_values_to_not_match_like_pattern",
            "expect_column_values_to_match_like_pattern_list",
            "expect_column_values_to_not_match_like_pattern_list",
            # "expect_column_values_to_match_strftime_format",
            "expect_column_values_to_be_dateutil_parseable",
            # "expect_column_values_to_be_json_parseable",
            # "expect_column_values_to_match_json_schema",
            "expect_column_distinct_values_to_be_in_set",
            # "expect_column_distinct_values_to_contain_set",
            # "expect_column_distinct_values_to_equal_set",
            # "expect_column_mean_to_be_between",
            # "expect_column_median_to_be_between",
            "expect_column_quantile_values_to_be_between",
            # "expect_column_stdev_to_be_between",
            # "expect_column_unique_value_count_to_be_between",
            # "expect_column_proportion_of_unique_values_to_be_between",
            "expect_column_most_common_value_to_be_in_set",
            # "expect_column_max_to_be_between",
            # "expect_column_min_to_be_between",
            # "expect_column_sum_to_be_between",
            "expect_column_pair_values_A_to_be_greater_than_B",
            "expect_column_pair_values_to_be_equal",
            "expect_column_pair_values_to_be_in_set",
            "expect_multicolumn_values_to_be_unique",
            "expect_multicolumn_sum_to_equal",
            "expect_column_pair_cramers_phi_value_to_be_less_than",
            # "expect_column_kl_divergence_to_be_less_than",
            "expect_column_bootstrapped_ks_test_p_value_to_be_greater_than",
            "expect_column_chisquare_test_p_value_to_be_greater_than",
            "expect_column_parameterized_distribution_ks_test_p_value_to_be_greater_than",
            "expect_compound_columns_to_be_unique",
        ]
    if context == "pandas":
        return expectation_type in [
            # "expect_table_columns_to_match_set",
            "expect_select_column_values_to_be_unique_within_record",
            "expect_table_column_count_to_be_between",
            "expect_table_column_count_to_equal",
            # "expect_column_to_exist",
            # "expect_table_columns_to_match_ordered_list",
            # "expect_table_row_count_to_be_between",
            # "expect_table_row_count_to_equal",
            "expect_table_row_count_to_equal_other_table",
            # "expect_column_values_to_be_unique",
            # "expect_column_values_to_not_be_null",
            # "expect_column_values_to_be_null",
            "expect_column_values_to_be_of_type",
            "expect_column_values_to_be_in_type_list",
            # "expect_column_values_to_be_in_set",
            # "expect_column_values_to_not_be_in_set",
            # "expect_column_values_to_be_between",
            # "expect_column_values_to_be_increasing",
            # "expect_column_values_to_be_decreasing",
            # "expect_column_value_lengths_to_be_between",
            # "expect_column_value_lengths_to_equal",
            # "expect_column_values_to_match_regex",
            # "expect_column_values_to_not_match_regex",
            # "expect_column_values_to_match_regex_list",
            # "expect_column_values_to_not_match_regex_list",
            "expect_column_values_to_match_like_pattern",
            "expect_column_values_to_not_match_like_pattern",
            "expect_column_values_to_match_like_pattern_list",
            "expect_column_values_to_not_match_like_pattern_list",
            # "expect_column_values_to_match_strftime_format",
            # "expect_column_values_to_be_dateutil_parseable",
            # "expect_column_values_to_be_json_parseable",
            # "expect_column_values_to_match_json_schema",
            "expect_column_distinct_values_to_be_in_set",
            # "expect_column_distinct_values_to_contain_set",
            # "expect_column_distinct_values_to_equal_set",
            # "expect_column_mean_to_be_between",
            # "expect_column_median_to_be_between",
            "expect_column_quantile_values_to_be_between",
            # "expect_column_stdev_to_be_between",
            # "expect_column_unique_value_count_to_be_between",
            # "expect_column_proportion_of_unique_values_to_be_between",
            "expect_column_most_common_value_to_be_in_set",
            # "expect_column_max_to_be_between",
            # "expect_column_min_to_be_between",
            # "expect_column_sum_to_be_between",
            "expect_column_pair_values_A_to_be_greater_than_B",
            "expect_column_pair_values_to_be_equal",
            "expect_column_pair_values_to_be_in_set",
            "expect_multicolumn_values_to_be_unique",
            "expect_multicolumn_sum_to_equal",
            "expect_column_pair_cramers_phi_value_to_be_less_than",
            # "expect_column_kl_divergence_to_be_less_than",
            "expect_column_bootstrapped_ks_test_p_value_to_be_greater_than",
            "expect_column_chisquare_test_p_value_to_be_greater_than",
            "expect_column_parameterized_distribution_ks_test_p_value_to_be_greater_than",
            "expect_compound_columns_to_be_unique",
        ]
    return False
