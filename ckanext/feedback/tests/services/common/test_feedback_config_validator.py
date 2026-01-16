import json

import pytest
from ckan.plugins import toolkit

from ckanext.feedback.services.common.config import FeedbackConfig


@pytest.mark.usefixtures("cleanup_feedback_config")
class TestSubModuleValidation:

    def test_feedback_config_not_dict(self):
        feedback_config = "not_a_dict"

        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'json object' in error_message.lower()

    def test_feedback_config_missing_modules_key(self):
        feedback_config = {"other_key": "value"}

        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'modules' in error_message.lower()

    def test_feedback_config_modules_not_dict(self):
        feedback_config = {"modules": "not_a_dict"}

        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'modules' in error_message.lower()
        assert 'object' in error_message.lower()

    def test_feedback_config_invalid_module_names(self):
        feedback_config = {"modules": {"invalid_module": {"enable": True}}}

        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'invalid_module' in error_message.lower()

    # utilizations.comments tests
    def test_utilizations_comment_valid(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {
                        "image_attachment": {"enable": True},
                        "reply_open": {"enable": False},
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_utilizations_comments_with_enable_orgs(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {
                        "image_attachment": {
                            "enable": True,
                            "enable_orgs": ["org1", "org2"],
                        }
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_utilizations_comments_with_disable_orgs(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {
                        "image_attachment": {
                            "enable": True,
                            "disable_orgs": ["org3", "org4"],
                        }
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_utilizations_comments_with_both_enable_and_disable_orgs(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {
                        "image_attachment": {
                            "enable": True,
                            "enable_orgs": ["org1", "org2"],
                            "disable_orgs": ["org3", "org4"],
                        }
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_utilizations_comments_not_dict(self):
        feedback_config = {
            "modules": {"utilizations": {"enable": True, "comments": "not_dict"}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'utilizations.comments' in error_message.lower()
        assert 'object' in error_message.lower() or 'dict' in error_message.lower()

    def test_submodule_with_only_disable_orgs(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {
                        "image_attachment": {
                            "enable": True,
                            "disable_orgs": ["org1", "org2", "org3"],
                        }
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_resources_comments_with_only_disable_orgs(self):
        feedback_config = {
            "modules": {
                "resources": {
                    "enable": True,
                    "comments": {
                        "rating": {"enable": True, "disable_orgs": ["org1", "org2"]}
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_submodule_with_all_optional_fields(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {
                        "image_attachment": {
                            "enable": True,
                            "enable_orgs": ["org1", "org2"],
                            "disable_orgs": ["org3", "org4"],
                        },
                        "reply_open": {
                            "enable": False,
                            "enable_orgs": ["org5"],
                            "disable_orgs": [],
                        },
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_enable_orgs_valid_list_simple(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {
                        "image_attachment": {
                            "enable": True,
                            "enable_orgs": ["test-org"],
                        }
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_validate_submodule_field_unsupported_type(self):
        from ckanext.feedback.services.common.feedback_config_validator import (
            validate_submodule_field,
        )

        with pytest.raises(toolkit.ValidationError) as exc_info:
            validate_submodule_field(
                field_name="test_field",
                field_value="some_value",
                expected_type=str,
                submodule_path="test.module",
            )

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'unsupported' in error_message.lower()
        assert 'str' in error_message.lower() or 'type' in error_message.lower()

    def test_resources_comments_with_all_fields(self):
        feedback_config = {
            "modules": {
                "resources": {
                    "enable": True,
                    "comments": {
                        "repeat_post_limit": {"enable": True, "enable_orgs": ["org1"]},
                        "rating": {"enable": True, "disable_orgs": ["org2"]},
                        "image_attachment": {
                            "enable": False,
                            "enable_orgs": ["org3"],
                            "disable_orgs": ["org4"],
                        },
                        "reply_open": {
                            "enable": True,
                            "enable_orgs": [],
                            "disable_orgs": [],
                        },
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)

        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_downloads_feedback_prompt_with_orgs_lists(self):
        feedback_config = {
            "modules": {
                "downloads": {
                    "enable": True,
                    "feedback_prompt": {
                        "modal": {
                            "enable": True,
                            "enable_orgs": ["org1", "org2", "org3"],
                            "disable_orgs": ["org4", "org5"],
                        }
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_utilizations_comments_invalid_submodule(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {
                        "invalid_submodule": {"enable": True},
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()
        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'invalid_submodule' in error_message.lower()
        assert 'utilizations.comments' in error_message.lower()

    def test_utilizations_comments_submodule_not_bool(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {"image_attachment": {"enable": "true"}},
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'enable' in error_message.lower()
        assert 'boolean' in error_message.lower() or 'bool' in error_message.lower()

    def test_utilizations_comments_submodule_not_dict(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {"image_attachment": "not_a_dict"},
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'image_attachment' in error_message.lower()
        assert 'object' in error_message.lower() or 'dict' in error_message.lower()

    def test_utilizations_without_comments_submodule(self):
        feedback_config = {"modules": {"utilizations": {"enable": True}}}
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_utilizations_comments_enable_orgs_not_list(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {
                        "image_attachment": {
                            "enable": True,
                            "enable_orgs": "not_a_list",
                        }
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'enable_orgs' in error_message.lower()
        assert 'list' in error_message.lower() or 'string' in error_message.lower()

    def test_utilizations_comments_enable_orgs_not_list_of_strings(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {
                        "image_attachment": {"enable": True, "enable_orgs": [1, 2, 3]}
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'enable_orgs' in error_message.lower()
        assert 'list' in error_message.lower() or 'string' in error_message.lower()

    # resources.comments tests

    def test_resources_comments_valid_structure(self):
        feedback_config = {
            "modules": {
                "resources": {
                    "enable": True,
                    "comments": {
                        "repeat_post_limit": {"enable": True},
                        "rating": {"enable": True},
                        "image_attachment": {"enable": False},
                        "reply_open": {"enable": True},
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_resources_comments_invalid_submodule(self):
        feedback_config = {
            "modules": {
                "resources": {
                    "enable": True,
                    "comments": {"invalid_submodule": {"enable": True}},
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'invalid_submodule' in error_message.lower()
        assert 'resources.comments' in error_message.lower()

    def test_resources_comments_rating_enable_not_bool(self):
        feedback_config = {
            "modules": {
                "resources": {"enable": True, "comments": {"rating": {"enable": 1}}}
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'enable' in error_message.lower()
        assert 'boolean' in error_message.lower() or 'bool' in error_message.lower()

    # downloads.feedback_prompt tests

    def test_download_feedback_prompt_valid_structure(self):
        feedback_config = {
            "modules": {
                "downloads": {
                    "enable": True,
                    "feedback_prompt": {"modal": {"enable": True}},
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_downloads_feedback_prompt_invalid_submodule(self):
        feedback_config = {
            "modules": {
                "downloads": {
                    "enable": True,
                    "feedback_prompt": {"invalid_submodule": {"enable": True}},
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        with pytest.raises(toolkit.ValidationError) as exc_info:
            FeedbackConfig().load_feedback_config()

        error_message = exc_info.value.__dict__.get('error_dict', {}).get('message', '')
        assert 'invalid_submodule' in error_message.lower()
        assert 'feedback_prompt' in error_message.lower()

    def test_downloads_feedback_prompt_modal_with_disable_orgs(self):
        feedback_config = {
            "modules": {
                "downloads": {
                    "enable": True,
                    "feedback_prompt": {
                        "modal": {"enable": True, "disable_orgs": ["org1", "org2"]}
                    },
                }
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    # Composite test (combination of multiple modules)

    def test_multiple_modules_with_submodules_valid(self):
        feedback_config = {
            "modules": {
                "utilizations": {
                    "enable": True,
                    "comments": {"image_attachment": {"enable": True}},
                },
                "resources": {
                    "enable": True,
                    "comments": {
                        "rating": {"enable": True},
                        "reply_open": {"enable": False},
                    },
                },
                "downloads": {
                    "enable": True,
                    "feedback_prompt": {"modal": {"enable": True}},
                },
            }
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_empty_submodule_is_valid(self):
        feedback_config = {
            "modules": {"utilizations": {"enable": True, "comments": {}}}
        }
        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True

    def test_module_without_submodule_structure(self):
        feedback_config = {
            "modules": {"likes": {"enable": True}, "recaptcha": {"enable": False}}
        }

        with open('/srv/app/feedback_config.json', 'w') as f:
            json.dump(feedback_config, f)
        FeedbackConfig().load_feedback_config()
        assert FeedbackConfig().is_feedback_config_file is True
