"""DB migration service configuration."""

from __future__ import annotations

from aicore.common.config import ConfigOptionsBuilder, connection_options, server_options


CONFIG_OPTIONS = (
    ConfigOptionsBuilder()
    .common_options("microservice_commons", "db")
    .start_section("Migration", 150)
    .create_options(
        lambda builder: server_options(builder, module_name="Migration", microservice_name="Upgrade", http_port=8141)
    )
    .create_options(lambda builder: connection_options(builder, server_name="Upgrade microservice", http_port=8141))
    .options
)
