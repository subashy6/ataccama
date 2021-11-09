"""Tools for generating files connected to AI Core properties."""

from __future__ import annotations

import json
import re

import alembic.config

from aicore.common.config import (
    CONFIGURATION_SERVICE_DOCUMENT_OPTIONS,
    ConfigurationError,
    PropertiesLoader,
    normalize_property_key,
)


CS_TYPE_MAPPINGS = {
    bool: "boolean",
    int: "number",
    float: "number",
}

MULTIPLE_SPACES_PATTERN = "\\s\\s+"


def json_one_line(value, deserializer):
    """Convert values that can span multiple lines and can be parsed as json to one-line string."""
    if deserializer not in [list, dict]:
        return value

    return json.dumps(json.loads(value), indent=0).replace("\n", "").replace(",", ", ")


def generate_config_json_property(option):
    """Generate single property for configService.json."""
    key = option["key"]
    property_type = CS_TYPE_MAPPINGS.get(option["deserializer"], "string")

    description = option["description"]
    description = re.sub(MULTIPLE_SPACES_PATTERN, " ", description)

    refreshable = option["refreshable"]
    description = f"{description} Refreshable: `{refreshable}`."

    default_value = option["default_value"]
    if default_value is not None:
        default_value = json_one_line(default_value, option["deserializer"])
        description = f"{description} Default value: `{default_value}`."

    return {
        "key": key,
        "type": property_type,
        "description": description,
    }


def generate_config_json(config_options):
    """Generate content for configService.json."""
    json_list = []
    for option in sorted(config_options.values(), key=lambda option: option["key"]):
        property_dict = generate_config_json_property(option)
        json_list.append(property_dict)

    return json_list


def generate_config_json_content():
    """Generate content for configService.json file."""
    config_options = collect_all_options()
    json_list = generate_config_json(config_options)
    content = {
        "_version": "0.1.0",
        "module": "aicore",
        "knownProperties": json_list,
    }

    return json.dumps(content, indent=2)


def generate_application_properties_property(option):
    """Generate single property for application.properties file."""
    key = option["key"]

    description = option["description"].replace("\n", "\n#")
    description = re.sub(MULTIPLE_SPACES_PATTERN, " ", description)

    refreshable = option["refreshable"]
    description = f"{description}\n# Refreshable: `{refreshable}`."

    value = option["default_value"]
    if value is not None:
        value = str(value).replace("\n", "\\\n")
        property_content = f"{key}={value}\n"
    else:
        property_content = f"#{key}=\n"

    return f"# {description}\n{property_content}"


def generate_application_properties_section(section, options):
    """Generate single section with config options for application.properties file."""
    properties = []

    for option in sorted(options, key=lambda option: option["key"]):
        if not option["document_only"]:
            property_content = generate_application_properties_property(option)
            properties.append(property_content)

    section_content = f"# ----------------------------- {section} -----------------------------\n"
    section_content += "\n".join(properties)
    return section_content


def generate_readme_property(option):
    """Generate single property for README.md file."""
    key = option["key"]
    property_type = CS_TYPE_MAPPINGS.get(option["deserializer"], "string").capitalize()
    refreshable = option["refreshable"]

    description = option["description"]
    description = re.sub(MULTIPLE_SPACES_PATTERN, " ", description)

    default_value = option["default_value"]
    if default_value is not None:
        default_value = json_one_line(default_value, option["deserializer"])
        description = f"{description}<br />Default value: `{default_value}`."

    return f"| `{key}` | {property_type} | {refreshable} | {description} |\n"


def generate_readme_section(section, options):
    """Generate single section with config options for README.md file."""
    properties = []

    for option in sorted(options, key=lambda option: option["key"]):
        property_content = generate_readme_property(option)
        properties.append(property_content)

    section_content = f"# {section} \n"
    section_content += "| Property    | Data Type   | Refreshable | Description |\n"
    section_content += "| ----------- | ----------- | ----------- | ----------- |\n"
    section_content += "".join(properties)
    return section_content


def group_options_by_section(config_options):
    """Group options by sections to which they belong."""
    sections_order = {}
    options_by_section = {}

    for option in config_options.values():
        section = option["section"]
        section_options = options_by_section.setdefault(section["name"], [])

        sections_order[section["name"]] = section["order"]
        section_options.append(option)

    return sections_order, options_by_section


def generate_application_properties_content():
    """Generate content for application.properties file."""
    config_options = collect_all_options()
    sections, options_by_section = group_options_by_section(config_options)
    sorted_section_names = [key for key, _ in sorted(sections.items(), key=lambda item: item[1])]
    sections_contents = [
        generate_application_properties_section(section, options_by_section[section])
        for section in sorted_section_names
    ]

    return "\n".join(sections_contents)


def generate_readme_content():
    """Generate content for README-properties.md file."""
    config_options = collect_all_options()
    sections, options_by_section = group_options_by_section(config_options)
    sorted_section_names = [key for key, _ in sorted(sections.items(), key=lambda item: item[1])]
    sections_contents = [
        generate_readme_section(section, options_by_section[section]) for section in sorted_section_names
    ]

    return "\n".join(sections_contents)


def collect_all_options():
    """Collect all existing config options (microservices, supervisor, options for loading configuration)."""
    from aicore.common.supervisor import CONFIG_OPTIONS as SUPERVISOR_CONFIG_OPTIONS
    from aicore.registry import get_all_config_options

    options = {}

    for microservice_config_options in get_all_config_options():
        for option in microservice_config_options.values():
            options[option["key"]] = option

    for other_options in [SUPERVISOR_CONFIG_OPTIONS, CONFIGURATION_SERVICE_DOCUMENT_OPTIONS]:
        for other_option in other_options.values():
            options[other_option["key"]] = other_option

    return options


def check_default_values(properties_file_path):
    """Check if values are set either as default value or in supplied properties file."""
    config_options = collect_all_options()
    local_properties = PropertiesLoader.load_properties_from_file(properties_file_path)

    for key, option in config_options.items():
        if option["default_value"] is not None or option["document_only"]:
            continue

        normalized_key = normalize_property_key(key)

        for local_key in local_properties:
            if local_key.startswith(normalized_key):
                break
        else:
            raise ConfigurationError(
                f"Invalid property {key}. Either specify default value, or put default value to {properties_file_path}."
            )


def alembic_config(connection_string, migrations_path):
    """Create Alembic configuration for database migration operations."""
    config = alembic.config.Config()
    config.set_main_option("script_location", migrations_path)
    config.set_main_option("sqlalchemy.url", connection_string)

    return config
