# ON/OFF Functionality

This document explains the ON/OFF functionality of the **ckanext-feedback** module and its features.

It is assumed that **ckanext-feedback** is already installed.  
If it is not yet installed, please follow the **Quick Start** instructions in the [README](../../README.md) to complete the installation.

## Feature Description

- You can toggle the ON/OFF of the following modules and features added by **ckanext-feedback**:
    - [utilization](./utilization.md)  
    Module related to data utilization methods  
    Default: 🟢**ON**

    - [resource](./resource.md)  
    Module related to comments on resources  
    Default: 🟢**ON**

    - [repeat post limit](./resource.md)  
    Feature to limit the number of comments per user to one per resource  
    Default: 🔴**OFF**

    - [rating](./resource.md)  
    Feature to rate resources  
    Default: 🔴**OFF**

    - [download](./download.md)  
    Module related to downloads  
    Default: 🟢**ON**

    ※ The ON/OFF of [repeat post limit](./resource.md) and [rating](./resource.md) can only be toggled if [resource](./resource.md) is 🟢**ON**.

## Configuration Method

- There are two ways to configure the ON/OFF of each module and feature:
    - Write the ON/OFF settings in `ckan.ini`.
    - Write the settings in `feedback_config.json` and place it in the CKAN environment.  
    ※ If you want to configure settings per organization, you can only do so with `feedback_config.json`.

### Configuration Priority

If both `ckan.ini` and `feedback_config.json` are configured, the settings in `feedback_config.json` will take precedence.  

(Example)  
Set modules and features to 🔴**OFF** in `ckan.ini`  
Set modules and features to 🟢**ON** in `feedback_config.json`  
→ Modules and features will be 🟢**ON**.  
(※ This behavior corresponds to interaction number 5 below.)

For details, refer to the **Interactions** and **Use Case Specific Configuration Table** below.  

### Interactions

This shows how the ON/OFF settings of modules and features are determined by the values written in `ckan.ini` and `feedback_config.json`.

- **ckan.ini**: The enable setting value of the module or feature written in `ckan.ini`.
- **feedback_config.json**: The enable setting value of the module or feature written in `feedback_config.json`.
- **ON/OFF**: The result of the ON/OFF setting of the module or feature.

| No. | ckan.ini | feedback_config.json | ON/OFF |
| :-: | :-: | :-: | :-: |
| 1 | - | - | Default value |
| 2 | ✔️True | - | 🟢ON |
| 3 | - | ✔️True | 🟢ON |
| 4 | ✔️True | ✔️True | 🟢ON |
| 5 | ❌False | ✔️True | 🟢ON |
| 6 | ❌False | - | 🔴OFF |
| 7 | - | ❌False | 🔴OFF |
| 8 | ✔️True | ❌False | 🔴OFF |
| 9 | ❌False | ❌False | 🔴OFF |

### Use Case Specific Configuration Table

When configuring with `feedback_config.json`, this shows how to apply the ON/OFF settings of modules and features for specific use cases.

- **enable**: The enable setting value of the module or feature written in `feedback_config.json`.
- **enable_orgs**: The list of organization names for which you want to set the module or feature to 🟢ON in `feedback_config.json`.
- **disable_orgs**: The list of organization names for which you want to set the module or feature to 🔴OFF in `feedback_config.json`.

| No. | Use Case | enable | enable_orgs | disable_orgs |
| :-: | :-: | :-: | :-: | :-: |
| 1 | When you want to set the module or feature to 🟢ON for all organizations | ✔️True | - | - |
| 2 | When you want to set the module or feature to 🔴OFF for all organizations | ❌False | - | - |
| 3 | When you want to set 🟢ON/🔴OFF per organization | ✔️True | ["org_name1", "org_name2"] | ["org_name3"] |
| 4 | When you want to set 🔴OFF for specific organizations only | ✔️True | - | ["org_name3"] |

※ If the same organization is listed in both **enable_orgs** and **disable_orgs**, the setting is inappropriate, and the module or feature for the corresponding organization will be 🔴**OFF**.

(Example)  
```json
{
        "enable_orgs": ["org_name1", "org_name2"],
        "disable_orgs": ["org_name1", "org_name3"]
}
```  
→ The setting for **"org_name1"** will be 🔴**OFF**

## Configuration Examples

### Configuring ON/OFF in `ckan.ini`

※ If you configure using this method, all modules and features for all organizations will be 🟢ON or 🔴OFF.  
※ If `feedback_config.json` is placed in the CKAN environment, this setting will not be reflected.

(Example) To set all modules and features to 🟢ON
```ini
・・・
## Plugins Settings ############################################################
ckan.plugins = xxxxx xxxxx xxxx xxxxx xxxxx feedback

ckan.feedback.utilization.enable = True
ckan.feedback.resources.enable = True
ckan.feedback.resources.comment.repeated_post_limit.enable = True
ckan.feedback.resources.comment.rating.enable = True
ckan.feedback.downloads.enable = True
・・・
```
| No. | Organization Name | utilization | resource | repeated_post_limit | rating | download |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | org_name1 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 2 | org_name2 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 3 | org_name3 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |

### Configuring ON/OFF in `feedback_config.json`

(Example) To set all modules and features to 🟢ON
```json
{
        "modules": {
                "utilizations": {
                        "enable": true
                },
                "resources": {
                        "enable": true,
                        "comments": {
                                "repeat_post_limit": {
                                        "enable": true
                                },
                                "rating": {
                                        "enable": true
                                }
                        }
                },
                "downloads": {
                        "enable": true
                }
        }
}
```
| No. | Organization Name | utilization | resource | repeated_post_limit | rating | download |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | org_name1 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 2 | org_name2 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 3 | org_name3 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |

(Example) To configure the ON/OFF of modules and features per organization
```json
{
        "modules":{
                "utilizations": {
                        "enable": true,
                        "enable_orgs": ["org_name1", "org_name2"],
                        "disable_orgs": ["org_name3"]
                },
                "resources": {
                        "enable": true,
                        "enable_orgs": ["org_name1", "org_name2"],
                        "disable_orgs": ["org_name3"],
                        "comments": {
                                "repeat_post_limit": {
                                        "enable": true,
                                        "enable_orgs": ["org_name1"],
                                        "disable_orgs": ["org_name2"]
                                },
                                "rating": {
                                        "enable": true,
                                        "enable_orgs": ["org_name1"],
                                        "disable_orgs": ["org_name2"]
                                }
                        }
                },
                "downloads": {
                        "enable": true,
                        "enable_orgs": ["org_name1", "org_name2"],
                        "disable_orgs": ["org_name3"]
                }
        }
}
```
| No. | Organization Name | utilization | resource | repeated_post_limit | rating | download |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | org_name1 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 2 | org_name2 | 🟢ON | 🟢ON | 🔴OFF | 🔴OFF | 🟢ON |
| 3 | org_name3 | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF |

## Integrating the download module with external plugins

When a resource is downloaded, the download module counts the number of downloads and then calls the default download callback `ckan.views.resource:download`.  
However, if you want to change that callback to a function from another extension (e.g., the download function of [googleanalytics](https://github.com/ckan/ckanext-googleanalytics)), you can replace it by specifying the target function in the `ckan.feedback.download_handler` setting variable in `ckan.ini`.

(Example) To use the download function of **ckanext-googleanalytics** with **ckanext-feedback**
    ```bash
    ckan.feedback.download_handler = ckanext.googleanalytics.views:download
    ```

Conversely, if you want to specify the download module of **ckanext-feedback** as the callback for another extension that can set an external handler, use `ckanext.feedback.views.download:download`.

(Example) To use the download function of **ckanext-feedback** with **ckanext-googleanalytics**
    ```bash
    googleanalytics.download_handler = ckanext.feedback.views.download:download
    ```

These integration methods are useful when using multiple extensions and paths like `/download` conflict.
