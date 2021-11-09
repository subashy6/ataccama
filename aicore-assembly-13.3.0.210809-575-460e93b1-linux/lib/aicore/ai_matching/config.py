"""Microservice configuration."""

from __future__ import annotations

import typing

from aicore.common.config import ConfigOptionsBuilder, connection_options, server_options


if typing.TYPE_CHECKING:
    from typing import Any


CONFIG_OPTIONS: dict[str, tuple[str, Any]] = (
    ConfigOptionsBuilder()
    .common_options("microservice_commons", "mmm")
    .start_section("AI Matching", 140)
    .create_options(
        lambda builder: server_options(
            builder, module_name="AI Matching", microservice_name="Matching Manager", grpc_port=8640, http_port=8140
        )
    )
    .create_options(
        lambda builder: connection_options(
            builder,
            server_name="Matching Manager microservice",
            grpc_port=8640,
            http_port=8140,
        )
    )
    .create_options(lambda builder: connection_options(builder, server_name="MDC", grpc_port=18581))
    .option(
        "initialization_sample_size",
        "ataccama.one.aicore.ai-matching.matching_steps.initialization.sample_size",
        int,
        "The number of records that are uniformly sampled from all the records fetched from MDM. Those records are the "
        "only ones used for initializing and training the AI Matching model.",
        default_value=int(1e6),
    )
    .option(
        "training_sample_size",
        "ataccama.one.aicore.ai-matching.matching_steps.initialization.training_sample_size",
        int,
        "The number of records that the AI Matching selects out of the records covered by the property "
        "`ai-matching.matching_steps.initialization.sample_size` for the actual training of the AI model. A higher "
        "value means that the model performs better, but the training takes more time.",
        default_value=40000,
    )
    .option(
        "groups_fetching_batch_size",
        "ataccama.one.aicore.ai-matching.matching_steps.evaluation.groups_fetching_batch_size",
        int,
        "The number of groups or clusters that are processed in a single batch when proposals are generated during the "
        "AI Matching evaluation. A higher number means that the processing is more efficient but requires more memory "
        "(RAM).",
        default_value=100,
    )
    .option(
        "scoring_batch_size",
        "ataccama.one.aicore.ai-matching.matching_steps.evaluation.scoring_batch_size",
        int,
        "The number of proposals that are processed in a single batch when proposals are scored during the AI Matching "
        "evaluation. A higher number means that the processing is more efficient but requires more memory (RAM).",
        default_value=5000,
    )
    .option(
        "decision_threshold",
        "ataccama.one.aicore.ai-matching.matching_steps.clustering.decision_threshold",
        float,
        "The dedupe clustering decision threshold that functions as a compromise between precision and recall. The "
        "value needs to be between `0` and `1`. Increasing the value means a higher precision and lower recall, that "
        "is, fewer `MERGE` proposals and more `SPLIT` proposals. Inversely, decreasing the value results in a lower "
        "level of precision and higher recall.",
        default_value=0.5,
    )
    .option(
        "max_columns",
        "ataccama.one.aicore.ai-matching.matching_steps.rules_extraction.max_columns",
        int,
        """The maximum number of columns in one extracted rule. A higher number means that the extracted rules can be
        more complex, that is, use more columns, but the rule extraction might take significantly longer.""",
        default_value=5,
    )
    .end_section()
    .options
)
