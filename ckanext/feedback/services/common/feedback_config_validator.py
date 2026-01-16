from ckan.plugins import toolkit

BASE_MODULE_SCHEMA = {
    'enable': bool,
    'enable_orgs': list,
    'disable_orgs': list,
}

UTILIZATIONS_COMMENTS_SCHEMA = {
    'valid_submodules': {'image_attachment', 'reply_open'},
    'submodule_structure': BASE_MODULE_SCHEMA,
}

RESOURCES_COMMENTS_SCHEMA = {
    'valid_submodules': {
        'repeat_post_limit',
        'rating',
        'image_attachment',
        'reply_open',
    },
    'submodule_structure': BASE_MODULE_SCHEMA,
}

DOWNLOADS_FEEDBACK_PROMPT_SCHEMA = {
    'valid_submodules': {'modal'},
    'submodule_structure': BASE_MODULE_SCHEMA,
}

MODULE_SUBMODULE_SCHEMAS = {
    'utilizations': {'comments': UTILIZATIONS_COMMENTS_SCHEMA},
    'resources': {'comments': RESOURCES_COMMENTS_SCHEMA},
    'downloads': {'feedback_prompt': DOWNLOADS_FEEDBACK_PROMPT_SCHEMA},
}

VALID_MODULE_NAMES = {
    'utilizations',
    'resources',
    'downloads',
    'likes',
    'moral_keeper_ai',
    'recaptcha',
    'notice',
}


def is_list_of_str(value):
    return isinstance(value, list) and all(isinstance(x, str) for x in value)


def validate_submodule_field(field_name, field_value, expected_type, submodule_path):
    # Validate fields of the submodule.

    if expected_type == bool:
        if not isinstance(field_value, bool):
            raise toolkit.ValidationError(
                {
                    "message": (
                        f"{submodule_path}.{field_name} must be a boolean"
                        f"got {type(field_value).__name__}"
                    )
                }
            )
    elif expected_type == list:
        if not is_list_of_str(field_value):
            raise toolkit.ValidationError(
                {
                    "message": (
                        f"{submodule_path}.{field_name} must be a list of strings,"
                        f"got {type(field_value).__name__}"
                    )
                }
            )
    # Defensive code for unsupported types
    else:
        raise toolkit.ValidationError(
            {
                "message": (
                    f"Unsupported field type '{expected_type}' for "
                    f"{submodule_path}.{field_name}. "
                    f"Supported types are: bool, list"
                )
            }
        )


def validate_submodule_structure(
    submodule_name, submodule_config, submodule_path, expected_structure
):

    if not isinstance(submodule_config, dict):
        raise toolkit.ValidationError(
            {
                "message": (
                    f"{submodule_path} must be an object, "
                    f"got {type(submodule_config).__name__}"
                )
            }
        )

    for field_name, expected_type in expected_structure.items():
        if field_name in submodule_config:
            validate_submodule_field(
                field_name=field_name,
                field_value=submodule_config[field_name],
                expected_type=expected_type,
                submodule_path=submodule_path,
            )


def validate_submodule(module_name, submodule_key, parent_config, schema):

    if submodule_key not in parent_config:
        return

    submodule_config = parent_config[submodule_key]
    parent_path = f"{module_name}.{submodule_key}"

    if not isinstance(submodule_config, dict):
        raise toolkit.ValidationError(
            {
                "message": (
                    f"{parent_path} must be an object, "
                    f"got {type(submodule_config).__name__}"
                )
            }
        )

    valid_submodules = schema['valid_submodules']
    actual_submodules = set(submodule_config.keys())
    invalid_submodules = actual_submodules - valid_submodules
    if invalid_submodules:
        raise toolkit.ValidationError(
            {
                "message": (
                    f"Invalid submodule names in {parent_path}: "
                    f"{sorted(invalid_submodules)}. "
                    f"Valid submodule names are: {sorted(valid_submodules)}"
                )
            }
        )

    expected_structure = schema['submodule_structure']
    for submodule_name in actual_submodules:
        submodule_path = f"{parent_path}.{submodule_name}"
        validate_submodule_structure(
            submodule_name=submodule_name,
            submodule_config=submodule_config[submodule_name],
            submodule_path=submodule_path,
            expected_structure=expected_structure,
        )


def validate_module_submodules(module_name, module_config):
    if module_name not in MODULE_SUBMODULE_SCHEMAS:
        return

    module_schemas = MODULE_SUBMODULE_SCHEMAS[module_name]

    for submodule_key, schema in module_schemas.items():
        validate_submodule(
            module_name=module_name,
            submodule_key=submodule_key,
            parent_config=module_config,
            schema=schema,
        )


def validate_feedback_config(feedback_config):
    if not isinstance(feedback_config, dict):
        raise toolkit.ValidationError(
            {"message": "feedback_config.json must be a JSON object"}
        )
    if "modules" not in feedback_config:
        raise toolkit.ValidationError(
            {"message": "feedback_config.json must have a 'modules' key"}
        )
    if not isinstance(feedback_config["modules"], dict):
        raise toolkit.ValidationError(
            {
                "message": (
                    "'modules' must be an object, "
                    f"got {type(feedback_config['modules']).__name__}"
                )
            }
        )
    actual_modules_names = set(feedback_config['modules'].keys())
    invalid_modules = actual_modules_names - VALID_MODULE_NAMES

    if invalid_modules:
        raise toolkit.ValidationError(
            {
                "message": (
                    f"Invalid module names found: {sorted(invalid_modules)}. "
                    f"Valid module names are: {sorted(VALID_MODULE_NAMES)}"
                )
            }
        )

    for module_name, module_config in feedback_config['modules'].items():
        validate_module_submodules(module_name, module_config)
