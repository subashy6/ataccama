"""Microservice configuration."""

from __future__ import annotations

from aicore.common.config import ConfigOptionsBuilder, connection_options, server_options


CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .common_options("microservice_commons", "db")
    .start_section("Term suggestions", 110)
    .create_options(
        lambda builder: server_options(
            builder, module_name="Term suggestions", microservice_name="Recommender", grpc_port=8541, http_port=8041
        )
    )
    .create_options(lambda builder: connection_options(builder, server_name="Recommender microservice", http_port=8041))
    .option(
        "recommender_batch_size",
        "ataccama.one.aicore.term-suggestions.recommender.batch-size",
        int,
        """The number of attributes for which term suggestions are recomputed at once by the Recommender service. If the
        batch size is too small, the database is queried too often and the computation is inefficient. If the batch size
        is too large, the process can take a long time, which in turn can render the Recommender unresponsive for the
        duration of the request and require more memory resources.""",
        default_value=1000,
    )
    .option(
        "recommender_target_accuracy",
        "ataccama.one.aicore.term-suggestions.recommender.target-accuracy",
        float,
        """The target ratio of term suggestions that users approved to the total number of suggestions, both approved and
        rejected, that the AI Core is trying to achieve. This is done by slowly adapting the similarity threshold for
        each term over time.""",
        default_value=0.8,
    )
    .option(
        "recommender_threshold_step",
        "ataccama.one.aicore.term-suggestions.recommender.threshold-step",
        float,
        """The speed at which the similarity threshold is adapted. The similarity threshold has a role in reaching the
        set `recommender.target-accuracy`.""",
        default_value=0.1,
    )
    .option(
        "recommender_default_threshold",
        "ataccama.one.aicore.term-suggestions.recommender.default-threshold",
        float,
        """The default starting distance threshold for newly created terms. The distance threshold defines how close
        the fingerprints need to be so that, if one of them has some terms assigned, the AI Core suggests those terms
        to the other one as well. It also affects the confidence of suggestions.""",
        default_value=1.0,
    )
    .option(
        "recommender_max_threshold",
        "ataccama.one.aicore.term-suggestions.recommender.max-threshold",
        float,
        """Sets the highest possible value for the similarity threshold (see the `recommender.target-accuracy` property).
        This value cannot be surpassed even when users consistently accept all term suggestions, which results
        in the AI Core attempting to further expand the threshold in order to lower the acceptance rate and meet
        the target accuracy.""",
        default_value=16,
    )
    .create_options(
        lambda builder: server_options(
            builder, module_name="Term suggestions", microservice_name="Neighbors", grpc_port=8542, http_port=8042
        )
    )
    .create_options(
        lambda builder: connection_options(
            builder, server_name="Neighbors microservice", grpc_port=8542, http_port=8042
        )
    )
    .option(
        "neighbors_index_limit",
        "ataccama.one.aicore.term-suggestions.neighbors.cache.attributes-limit",
        int,
        """The maximum number of fingerprints that can be present in the index used for searching neighbors.
        Once this value is reached, the microservice shuts down when trying to add new attributes. If the number
        of attributes in the database, including the deleted ones, exceeds the limit on startup, the microservice waits
        in the Not ready state indefinitely or until the number of attributes is reduced to this value or lower.""",
        default_value=1_000_000,
    )
    .create_options(
        lambda builder: server_options(
            builder, module_name="Term suggestions", microservice_name="Feedback", grpc_port=8543, http_port=8043
        )
    )
    .create_options(lambda builder: connection_options(builder, server_name="Feedback microservice", http_port=8043))
    .option(
        "feedback_batch_size",
        "ataccama.one.aicore.term-suggestions.feedback.batch-size",
        int,
        """The number of feedbacks for which thresholds are recomputed at once by the Feedback service. If the
        batch size is too small, the database is queried too often and the computation is inefficient. If the batch size
        is too large, the Feedback service can in turn require more memory resources.""",
        default_value=10_000,
    )
    .end_section()
    .options
)
