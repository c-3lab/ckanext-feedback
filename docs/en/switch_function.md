# ON/OFF Feature Configuration

This document explains the ON/OFF settings for modules and features in **ckanext-feedback**.

> [!NOTE]
> This assumes that **ckanext-feedback** is already installed.  
> If installation is not yet complete, please complete the installation by following the **Quick Start** described in the [README](../../README.md).

## Overview

You can toggle ON/OFF for the following modules and features added by **ckanext-feedback**:

#### Main Modules

- **[utilization](./utilization.md)** - Module related to data utilization methods  
  **Default**: 🟢**ON**

- **[resource](./resource.md)** - Module related to comments on resources  
  **Default**: 🟢**ON**

- **[download](./download.md)** - Module related to downloads  
  **Default**: 🟢**ON**

- **[like](./likes.md)** - Module for liking resources  
  **Default**: 🟢**ON**

- **[moral-keeper-ai](./moral_keeper_ai.md)** - AI feature module  
  **Default**: 🔴**OFF**
#### Utilization Module Sub-features
> [!IMPORTANT]
> The following features can only be toggled ON/OFF when [utilization](./utilization.md) is 🟢**ON**.

- **[image attachment](./utilization.md)** - Feature to attach images to utilization comments  
  **Default**: 🟢**ON**

- **[reply_open](./utilization.md)** - Feature allowing non-administrators to reply to comments  
  **Default**: 🔴**OFF**

#### Resource Module Sub-features

> [!IMPORTANT]
> The following features can only be toggled ON/OFF when [resource](./resource.md) is 🟢**ON**.

- **[repeat post limit](./resource.md)** - Feature limiting each user to commenting once per resource  
  **Default**: 🔴**OFF**

- **[rating](./resource.md)** - Feature for rating resources  
  **Default**: 🔴**OFF**

- **[image attachment](./resource.md)** - Feature to attach images to comments  
  **Default**: 🔴**OFF**

- **[reply_open](./resource.md)** - Feature allowing non-administrators to reply to comments  
  **Default**: 🔴**OFF**
  
#### Download Module Sub-features
> [!IMPORTANT]
> The following features can only be toggled ON/OFF when [download](./download.md) is 🟢**ON**.

- **[feedback_prompt](./download.md)** - Feature displaying a modal window requesting feedback when downloading  
  **Default**: 🟢**ON**


## Configuration

### 2 Configuration Methods

There are two ways to configure ON/OFF for each module and feature:

#### 1. Configuration via `ckan.ini`

Configuration example:
```ini
ckan.feedback.utilization.enable = True
```

#### 2. Configuration via `feedback_config.json`

Create `feedback_config.json` and place it on the server.

**Sample file**: [feedback_config_sample.json](https://github.com/c-3lab/ckanext-feedback/blob/d49b6ff2eeeb5e579194efe5315a0c5b3935df8d/feedback_config_sample.json)

**Placement location**:
- **Default**: `/srv/app` directory
- **Custom**: If placing in a directory other than `/srv/app`, describe the following configuration in `ckan.ini`:

```ini
ckan.feedback.config_file = path/to/feedback_config_dir
```

**Configuration example**:
```json
{
    "modules": {
        "utilizations": {
            "enable": true
        }
    }
}
```

> [!TIP]
> Organization-specific settings can only be configured via `feedback_config.json`.

### Configuration Priority

#### Overwriting with `feedback_config.json` Configuration

Even if configured in `ckan.ini`, if `feedback_config.json` exists on the server, settings will be overwritten based on the contents of `feedback_config.json`.

**Example**:
- Configure modules or features 🔴**OFF** in `ckan.ini`
- Configure modules or features 🟢**ON** in `feedback_config.json`
- → Modules or features will be 🟢**ON**

> [!NOTE]
> This behavior corresponds to number 5 in the **Interactions** below.

## Interactions

Shows how ON/OFF settings for modules and features are determined by values described in `ckan.ini` and `feedback_config.json`.

### Interaction Table

| No. | ckan.ini | feedback_config.json | ON/OFF |
| :-: | :-: | :-: | :-: |
| 1 | Not described | No file※1 | Default value |
| 2 | ✔️True | No file※1 | 🟢ON |
| 3 | Not described | ✔️True | 🟢ON |
| 4 | ✔️True | ✔️True | 🟢ON |
| 5 | ❌False | ✔️True | 🟢ON |
| 6 | ❌False | No file※1 | 🔴OFF |
| 7 | Not described | ❌False | 🔴OFF |
| 8 | ✔️True | ❌False | 🔴OFF |
| 9 | ❌False | ❌False | 🔴OFF |
| 10 | ✔️True | Not described※2 | Default value (`ckan.ini` is ignored) |
| 11 | ❌False | Not described※2 | Default value (`ckan.ini` is ignored) |

**Legend**:
- ※1: "No file" indicates that `feedback_config.json` does not exist on the server
- ※2: "Not described" indicates that `feedback_config.json` exists on the server but configuration values are not described

## Organization-specific Configuration

### Configuring ON/OFF for Each Organization

You can configure ON/OFF for modules for each organization using `feedback_config.json`.

> [!TIP]
> **Organization name** refers to the value included in the organization page URL (e.g., demo.ckan.org/organization/**org_name**) created when creating an organization in the CKAN environment. More precisely, it corresponds to the name in the Group table in the CKAN database.

**Configuration example**:
```json
{
    "modules":{
        "utilizations": {
            "enable": true,
            "disable_orgs": ["org_name"]
        }
    }
}
```

### Configuration Application Table by Use Case

When configuring using `feedback_config.json`, shows how to apply ON/OFF settings for modules and features for each specific use case.

| No. | Use Case | enable | enable_orgs | disable_orgs |
| :-: | :-: | :-: | :-: | :-: |
| 1 | When you want to turn modules or features 🟢ON for all organizations | ✔️True | Don't describe | Don't describe |
| 2 | When you want to turn modules or features 🔴OFF for all organizations | ❌False | Don't describe | Don't describe |
| 3 | When you want to turn 🔴OFF only for specific organizations | ✔️True | Don't describe | ["**org_name2**"] |
| 4 | When you want to turn 🟢ON only for specific organizations | ✔️True | ["**org_name1**"]  | Don't describe |

> [!WARNING] 
> If you list the same organization in both **enable_orgs** and **disable_orgs**, only the **disable_orgs** setting will be reflected and the **enable_orgs** setting will be ignored.
> 
> **Example**:
> ```json
> {
>     "enable": true,
>     "enable_orgs": ["org_name1", "org_name2"],
>     "disable_orgs": ["org_name1", "org_name3"]
> }
> ```  
> → **org_name1** and **org_name3** settings will be 🔴**OFF**, and other organizations like **org_name2** will be 🟢**ON**.

## Configuration Examples

Shows configuration examples for `ckan.ini` and `feedback_config.json`.  
The CKAN environment in the configuration examples assumes three organizations (org_name1, org_name2, org_name3).

### Configuring ON/OFF in `ckan.ini`

> [!NOTE]
> When configuring this way, modules and features for all organizations will be 🟢ON or 🔴OFF.  
> If `feedback_config.json` is placed in the CKAN environment, this configuration will not be reflected.

**Example**: When turning all modules and features 🟢ON
```ini
・・・
## Plugins Settings ############################################################
ckan.plugins = xxxxx xxxxx xxxx xxxxx xxxxx feedback

ckan.feedback.utilization.enable = True
ckan.feedback.utilization.comments.image_attachment.enable = True
ckan.feedback.resources.enable = True
ckan.feedback.resources.comment.repeated_post_limit.enable = True
ckan.feedback.resources.comment.rating.enable = True
ckan.feedback.resources.comment.image_attachment.enable = True
ckan.feedback.downloads.enable = True
ckan.feedback.downloads.modal.enable = True
ckan.feedback.likes.enable = True
ckan.feedback.moral_keeper_ai.enable = True
・・・
```

| No. | Organization Name | utilization | utilization_comment_image_attachment | utilization_comment_reply_open | resource | repeated_post_limit | rating | resource_comment_image_attachment | resource_comment_reply_open | download | modal | like | moral-keeper-ai |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | org_name1 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |🟢ON | 🟢ON |
| 2 | org_name2 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |🟢ON | 🟢ON |
| 3 | org_name3 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |🟢ON | 🟢ON |


### Configuring ON/OFF in `feedback_config.json`

#### Example 1: When turning all modules and features 🟢ON

```json
{
    "modules": {
        "utilizations": {
            "enable": true,
            "comments": {
                "image_attachment": {
                    "enable": true
                },
                "reply_open": {
                    "enable": true
                }
            }
        },
        "resources": {
            "enable": true,
            "comments": {
                "repeat_post_limit": {
                    "enable": true
                },
                "rating": {
                    "enable": true
                },
                "image_attachment": {
                    "enable": true
                },
                "reply_open": {
                    "enable": true
                }
            }
        },
        "downloads": {
            "enable": true,
            "feedback_prompt": {
                "modal": {
                    "enable": true
                }
            }
        },
        "likes": {
            "enable": true
        },
        "moral_keeper_ai": {
            "enable": true
        }
    }
}
```


| No. | Organization Name | utilization | utilization_comment_image_attachment | utilization_comment_reply_open | resource | repeated_post_limit | rating | resource_comment_image_attachment | resource_comment_reply_open | download | modal | like | moral-keeper-ai |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | org_name1 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |🟢ON | 🟢ON |
| 2 | org_name2 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |🟢ON | 🟢ON |
| 3 | org_name3 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |🟢ON | 🟢ON |


#### Example 2: When configuring ON/OFF for modules and features per organization

```json
{
        "modules":{
            "utilizations": {
                "enable": true,
                "disable_orgs": ["org_name3"],
                "comments" : {
                    "image_attachment":{
                        "enable" :true,
                        "enable_orgs": ["org_name1"]
                }
            },
            "resources": {
                "enable": true,
                "disable_orgs": ["org_name3"],
                "comments": {
                    "repeat_post_limit": {
                        "enable": true,
                        "enable_orgs": ["org_name1"]
                    },
                    "rating": {
                        "enable": true,
                        "enable_orgs": ["org_name1"]
                    },
                    "image_attachment": {
                        "enable": true,
                        "enable_orgs": ["org_name1"]
                    }
                }
            },
            "downloads": {
                "enable": true,
                "disable_orgs":  ["org_name2", "org_name3"],
                    "feedback_prompt":{
                        "modal":{
                            "enable":true,
                            "disable_orgs":  ["org_name2", "org_name3"]
                    }
                }
            },
            "likes": {
                "enable": true,
                "disable_orgs": ["org_name2", "org_name3"]
            },
            "moral_keeper_ai": {
                "enable": true,
                "enable_orgs": ["org_name1"]
            }
        }
    }
}
```


| No. | Organization Name | utilization | utilization_comment_image_attachment | utilization_comment_reply_open | resource | repeated_post_limit | rating | resource_comment_image_attachment | resource_comment_reply_open | download | modal | like | moral-keeper-ai |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | org_name1 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 2 | org_name2 | 🟢ON | 🟢ON | 🔴OFF | 🔴OFF | 🔴OFF | 🟢ON | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF |
| 3 | org_name3 | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF |


## Integration with External Plugins

### Integrating download module with external plugins

When a resource is downloaded, the download module performs download count processing and then calls the default download callback `ckan.views.resource:download`.

However, if you want to change that callback to a function from another Extension (e.g., the download function from [googleanalytics](https://github.com/ckan/ckanext-googleanalytics)), you can specify the target function in the `ckan.ini` configuration variable `ckan.feedback.download_handler` to replace it.

**Example**: When you want to use **ckanext-googleanalytics** download function with **ckanext-feedback**
```ini
ckan.feedback.download_handler = ckanext.googleanalytics.views:download
```

Conversely, if you want to specify **ckanext-feedback**'s download module as a callback for other Extensions that can configure external handlers, you can use `ckanext.feedback.views.download:download`.

**Example**: When you want to use **ckanext-feedback** download function with **ckanext-googleanalytics**
```ini
googleanalytics.download_handler = ckanext.feedback.views.download:download
```

> [!TIP]
> These integration methods are useful when paths like `/download` conflict when using multiple extensions.

