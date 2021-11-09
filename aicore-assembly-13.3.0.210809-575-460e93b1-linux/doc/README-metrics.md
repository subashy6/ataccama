| Component | Metric | Type | Description | Labels |
| ----------- | ----------- | ----------- | ----------- | ----------- |
| ai_ad | ataccama_one_aicore_ai_ad_n_ad_requests_total | counter | The number of requests for anomaly detection issued from MMM. | `[]` |
| ai_ad | ataccama_one_aicore_ai_ad_duration_of_get_history_from_mmm_command_seconds | summary | The number of seconds needed for fetching and processing data from MMM. | `[]` |
| ai_ad | ataccama_one_aicore_ai_ad_n_fetched_data_points_total | summary | The number of data points (for example, profiling versions) that were fetched from MMM. | `[]` |
| ai_ad | ataccama_one_aicore_ai_ad_duration_of_ad_per_model_seconds | summary | The number of seconds needed to complete anomaly detection processing for the chosen model. | `['model_type']` |
| ai_ad | ataccama_one_aicore_ai_ad_n_positive_anomaly_feedbacks_total | summary | The number of confirmed anomalies (feedback) that users provided. | `[]` |
| ai_ad | ataccama_one_aicore_ai_ad_n_detected_anomalous_data_points_total | summary | The number of data points that were identified as anomalous by the model. | `[]` |
| ai_aim | ataccama_one_aicore_ai_aim_n_manager_instances | gauge | The number of active instances. | `[]` |
| ai_aim | ataccama_one_aicore_ai_aim_step_processing_seconds | gauge | The computation time of each matching step for each instance, expressed in seconds. | `['matching_step', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_columns | summary | The number of columns provided. | `['matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_rows | gauge | The number of rows provided in phases `INITIALIZING_MATCHING` and `FETCHING_RECORDS`. | `['type', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_method_processing_seconds | gauge | The processing time of each method in a matching step for each instance, expressed in seconds. | `['method', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_blocking_rules | gauge | The number of blocking rules used. | `['matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_blocking_rules_functions | gauge | The number of occurrences for each blocking rule function. | `['blocking_rule_function', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_blocking_rules_types | gauge | The number of occurrences for each blocking rule type: `simple` and `compound`. | `['type', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_training_pairs_per_decision | gauge | The number of training pairs provided for each AI decision. | `['decision', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_model_quality | gauge | The model quality represented as a floating point value between 0 and 1. | `['matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_rule_coverage | histogram | A floating point value between 0 and 1 representing the percentage of matches covered by the current set of extracted rules. | `['matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_rule_extraction_iteration_rules_generated | gauge | The number of rules generated in one iteration of rule extraction. | `['matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_rule_extraction_iteration | gauge | The number of n column rules of type `VALID`, `INVALID`, and `REDUNDANT` for one iteration of rule extraction. | `['type', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_rule_extraction_iteration_processing_seconds | gauge | The computation time of each iteration of rule extraction, expressed in seconds. | `['matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_rule_extraction_rules_total | gauge | The total number of rules of type `GENERATED`, `EVALUATED`, and `EXTRACTED` used for rule extraction. | `['type', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_rule_extraction_pairs_total | gauge | The total number of pairs of type `POSITIVE`, `NEGATIVE`, and `COVERED` used for rule extraction. | `['type', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_rule_extraction_total_processing_seconds | gauge | The computation time of type `GENERATION`, `EVALUATION`, and `EXTRACTION` needed for a complete rule extraction run, expressed in seconds. | `['type', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_rules_min_confidences | gauge | The minimum confidence level for rule extraction of type `MATCH` and `DISTINCT`. | `['type', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_rules_per_category | gauge | The number of parametric rules extracted for categories `PARAMETRIC`, `NON_PARAMETRIC`, and `COMPOSITION`. | `['type', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_extract_rules_command_calls | counter | The number of times that the rule extraction command was called. | `['matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_composition_rules_depth | gauge | The number of simple rules contained in one composition rule. | `['matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_proposals | gauge | The number of proposals of type `GENERATED` for `MATCH` and `SPLIT/DISTINCT` decisions. | `['type', 'decision', 'matching_id']` |
| ai_aim | ataccama_one_aicore_ai_aim_n_evaluate_records_matching_command_calls | counter | The number of times the command for generating proposals was called. | `['matching_id']` |
| ai_ts_feedback | ataccama_one_aicore_ai_ts_feedback_feedbacks_total | counter | The total number of positive or negative feedbacks received from users. | `['type']` |
| ai_ts_feedback | ataccama_one_aicore_ai_ts_feedback_thresholds | histogram | The current distance thresholds. | `[]` |
| ai_ts_neighbors | ataccama_one_aicore_ai_ts_neighbors_database_attributes_present | gauge | The number of attributes available to the Term Suggestions microservices. Warning: The value might be overestimated. | `[]` |
| ai_ts_neighbors | ataccama_one_aicore_ai_ts_neighbors_index_attributes_present | gauge | The number of attributes currently stored in the memory. | `[]` |
| ai_ts_neighbors | ataccama_one_aicore_ai_ts_neighbors_index_attributes_limit | gauge | The maximum number of attributes that can be stored in the memory. | `[]` |
| ai_ts_neighbors | ataccama_one_aicore_ai_ts_neighbors_neighbors_distances | histogram | Distances to k-th nearest neighbors. | `['k']` |
| ai_ts_recommender | ataccama_one_aicore_ai_ts_recommender_attributes_processed_total | counter | The number of attributes for which suggestions were computed. | `[]` |
| ai_ts_recommender | ataccama_one_aicore_ai_ts_recommender_suggestions_created_total | counter | The number of suggestions created. | `[]` |
| ai_ts_recommender | ataccama_one_aicore_ai_ts_recommender_terms_known | gauge | The number of known terms. | `[]` |
| ai_ts_recommender | ataccama_one_aicore_ai_ts_recommender_terms_disabled | gauge | The number of disabled terms. | `[]` |
| ai_ts_recommender | ataccama_one_aicore_ai_ts_recommender_recommendation_starts_total | counter | The number of times all suggestions were rendered outdated. | `[]` |
| ai_ts_recommender | ataccama_one_aicore_ai_ts_recommender_recommendation_finishes_total | counter | The number of times all suggestions were brought up to date. | `[]` |
| ai_ts_recommender | ataccama_one_aicore_ai_ts_recommender_recommendation_progress | gauge | The number of attributes that have up-to-date suggestions. | `[]` |
| ai_ts_recommender | ataccama_one_aicore_ai_ts_recommender_recommendation_progress_with_ground_truth | gauge | The number of attributes that have up-to-date suggestions and for which the ground truth is known. | `[]` |
| ai_ts_recommender | ataccama_one_aicore_ai_ts_recommender_suggestions_confusion_matrix | gauge | The confusion matrix computed between suggestions and assigned terms. | `['entry']` |
| database | ataccama_one_aicore_database_query_seconds | summary | The number of seconds a database query takes to complete. | `['operation']` |
| graphql_client | ataccama_one_aicore_graphql_client_query_seconds | summary | The number of seconds a GraphQL query takes to complete. | `[]` |
| grpc_client | ataccama_one_aicore_grpc_client_query_seconds | summary | The number of seconds a gRPC query takes to complete. | `[]` |
| grpc_server | ataccama_one_aicore_grpc_server_auth_failures_total | counter | The total number of gRPC requests with authentication failures. | `[]` |
| grpc_server | ataccama_one_aicore_grpc_server_commands_total | counter | The total number of gRPC commands received. | `['type']` |
| grpc_server | ataccama_one_aicore_grpc_server_processing_seconds | summary | The processing time of a gRPC request, expressed in seconds. | `['stage']` |
| grpc_server | ataccama_one_aicore_grpc_server_queue_size | gauge | The number of active RPCs, either queued or currently processed. | `[]` |
| microservice | ataccama_one_aicore_microservice_microservice | info | The microservice details. | `[]` |
| wsgi_server | ataccama_one_aicore_wsgi_server_auth_failures_total | counter | The total number of HTTP requests with authentication failures. | `[]` |
| wsgi_server | ataccama_one_aicore_wsgi_server_requests_total | counter | The total number of HTTP request status codes.  | `['status']` |
