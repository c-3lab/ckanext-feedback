# ON/OFF 機能設定

本ドキュメントでは、**ckanext-feedback**のモジュールと機能に関するON/OFF設定について説明します。

> [!NOTE]
> **ckanext-feedback**は既にインストール済みであることを前提としています。  
> まだインストールが完了していない場合は、[README](../../README.md)に記載の**クイックスタート**に従い、インストールを完了させてください。

## 概要

**ckanext-feedback**で追加された以下のモジュールや機能のON/OFFを切り替えることができます：

#### 主要モジュール

- **[utilization](./utilization.md)** - データの利活用方法に関するモジュール  
  **デフォルト**: 🟢**ON**

- **[resource](./resource.md)** - リソースへのコメントに関するモジュール  
  **デフォルト**: 🟢**ON**

- **[download](./download.md)** - ダウンロードに関するモジュール  
  **デフォルト**: 🟢**ON**

- **[like](./likes.md)** - リソースにいいねを行うモジュール  
  **デフォルト**: 🟢**ON**

- **[moral-keeper-ai](./moral_keeper_ai.md)** - AI機能モジュール  
  **デフォルト**: 🔴**OFF**
#### Utilization モジュールのサブ機能
> [!IMPORTANT]
> 以下の機能は、[utilization](./utilization.md)が🟢**ON**になっている場合にのみON/OFFを切り替えることができます。

- **[image attachment](./utilization.md)** - 利活用方法へのコメントに画像を添付する機能  
  **デフォルト**: 🟢**ON**

#### Resource モジュールのサブ機能

> [!IMPORTANT]
> 以下の機能は、[resource](./resource.md)が🟢**ON**になっている場合にのみON/OFFを切り替えることができます。

- **[repeat post limit](./resource.md)** - 1つのリソースに対してコメントできる回数を各ユーザーごとに1回に制限する機能  
  **デフォルト**: 🔴**OFF**

- **[rating](./resource.md)** - リソースへの評価を行う機能  
  **デフォルト**: 🔴**OFF**

- **[image attachment](./resource.md)** - コメントに画像を添付する機能  
  **デフォルト**: 🔴**OFF**
#### Download モジュールのサブ機能
> [!IMPORTANT]
> 以下の機能は、[download](./download.md)が🟢**ON**になっている場合にのみON/OFFを切り替えることができます。

- **[feedback_prompt](./download.md)** - ダウンロード時にフィードバックを求めるモーダルウィンドウが表示される機能  
  **デフォルト**: 🟢**ON**

## 設定方法

### 2通りの設定方法

各モジュールと機能のON/OFFを設定するには、以下の2通りの方法があります：

#### 1. `ckan.ini`による設定

設定例：
```ini
ckan.feedback.utilization.enable = True
```

#### 2. `feedback_config.json`による設定

`feedback_config.json`を作成し、サーバー内に配置してください。

**サンプルファイル**: [feedback_config_sample.json](https://github.com/c-3lab/ckanext-feedback/blob/d49b6ff2eeeb5e579194efe5315a0c5b3935df8d/feedback_config_sample.json)

**配置場所**:
- **デフォルト**: `/srv/app`ディレクトリ
- **カスタム**: `/srv/app`以外のディレクトリに配置する場合は、`ckan.ini`に以下の設定を記述してください：

```ini
ckan.feedback.config_file = path/to/feedback_config_dir
```

**設定例**:
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
> 組織毎の設定を行いたい場合は、`feedback_config.json`でのみ設定することができます。

### 設定の優先順位

#### `feedback_config.json`による設定の上書き

`ckan.ini`に本設定がされていても、`feedback_config.json`がサーバー内に存在する場合は、`feedback_config.json`の内容をもとに設定が上書きされます。

**例**:
- `ckan.ini`でモジュールや機能を🔴**OFF**に設定
- `feedback_config.json`でモジュールや機能を🟢**ON**に設定
- → モジュールや機能は🟢**ON**になります

> [!NOTE]
> この動作は、以下の**相互作用**の5番に該当します。

## 相互作用

モジュールや機能のON/OFF設定が、`ckan.ini`と`feedback_config.json`のそれぞれに記述された値によってどのように決定されるかを示しています。

### 相互作用表

| No. | ckan.ini | feedback_config.json | ON/OFF |
| :-: | :-: | :-: | :-: |
| 1 | 記述なし | ファイルなし※1 | デフォルト値 |
| 2 | ✔️True | ファイルなし※1 | 🟢ON |
| 3 | 記述なし | ✔️True | 🟢ON |
| 4 | ✔️True | ✔️True | 🟢ON |
| 5 | ❌False | ✔️True | 🟢ON |
| 6 | ❌False | ファイルなし※1 | 🔴OFF |
| 7 | 記述なし | ❌False | 🔴OFF |
| 8 | ✔️True | ❌False | 🔴OFF |
| 9 | ❌False | ❌False | 🔴OFF |
| 10 | ✔️True | 記述なし※2 | デフォルト値（`ckan.ini`は無視される） |
| 11 | ❌False | 記述なし※2 | デフォルト値（`ckan.ini`は無視される） |

**凡例**:
- ※1：「ファイルなし」は、`feedback_config.json`がサーバー内に存在しないことを示します
- ※2：「記述なし」は、`feedback_config.json`はサーバー内に存在するが、設定値の記述がない場合を示します

## 組織別設定

### 組織ごとのモジュールのON/OFFを設定する

`feedback_config.json`を用いて、組織ごとにモジュールのON/OFFを設定することができます。

> [!TIP]
> **組織の名前**とは、CKAN環境で組織作成時に作成される、組織ページのURL（例：demo.ckan.org/organization/**org_name**）に含まれる値にあたります。より厳密には、CKANのデータベースのGroupテーブルのnameに該当します。

**設定例**:
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

### ユースケース別設定適用表

`feedback_config.json`を用いて設定する際、特定のユースケース毎にモジュールや機能のON/OFF設定をどのように適用するかを示しています。

| No. | ユースケース | enable | enable_orgs | disable_orgs |
| :-: | :-: | :-: | :-: | :-: |
| 1 | 全ての組織でモジュールや機能を🟢ONにしたい場合 | ✔️True | 記述しない | 記述しない |
| 2 | 全ての組織でモジュールや機能を🔴OFFにしたい場合 | ❌False | 記述しない | 記述しない |
| 3 | 特定の組織のみ🔴OFFにしたい場合 | ✔️True | 記述しない | ["**org_name2**"] |
| 4 | 特定の組織のみ🟢ONにしたい場合 | ✔️True | ["**org_name1**"]  | 記述しない |

> [!WARNING] 
> **enable_orgs**と**disable_orgs**に同じ組織を記載した場合、**disable_orgs**の設定のみが反映され、**enable_orgs**の設定は無視されます。
> 
> **例**:
> ```json
> {
>     "enable": true,
>     "enable_orgs": ["org_name1", "org_name2"],
>     "disable_orgs": ["org_name1", "org_name3"]
> }
> ```  
> → **org_name1**と**org_name3**の設定は🔴**OFF**になり、それ以外の組織である**org_name2**は🟢**ON**になります。

## 設定例

`ckan.ini`と`feedback_config.json`で、それぞれの設定例を示します。  
設定例のCKAN環境には、3つの組織（org_name1、org_name2、org_name3）があるとしています。

### `ckan.ini`でON/OFFの設定を行う

> [!NOTE]
> この方法で設定を行った場合はすべての組織のモジュールや機能は🟢ONまたは🔴OFFになります。  
> `feedback_config.json`がCKAN環境に配置されている場合は本設定は反映されません。

**例**: すべてのモジュールや機能を🟢ONにする場合
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
ckan.feedback.download.modal.enable = True
ckan.feedback.likes.enable = True
ckan.feedback.moral_keeper_ai.enable = True
・・・
```

| No. | 組織名 | utilization | utilization_comment_image_attachment | resource | repeated_post_limit | rating | resource_comment_image_attachment | download | modal | like | moral-keeper-ai |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | org_name1 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 2 | org_name2 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 3 | org_name3 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |

### `feedback_config.json`でON/OFFの設定を行う

#### 例1: すべてのモジュールや機能を🟢ONにする場合

```json
{
    "modules": {
        "utilizations": {
            "enable": true,
            "comments": {
                "image_attachment"  :{
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
                }
            }
        },
        "downloads": {
            "enable": true
            "feedback_prompt":{
                "modal":{
                    "enable":true
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

| No. | 組織名 | utilization | utilization_comment_image_attachment | resource | repeated_post_limit | rating | resource_comment_image_attachment | download | modal | like | moral-keeper-ai |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | org_name1 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 2 | org_name2 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 3 | org_name3 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |

#### 例2: 組織毎にモジュールや機能のON/OFFを設定する場合

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

| No. | 組織名 | utilization | utilization_comment_image_attachment | resource | repeated_post_limit | rating | resource_comment_image_attachment | download | modal | like | moral-keeper-ai |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | org_name1 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 2 | org_name2 | 🟢ON | 🟢ON | 🔴OFF | 🔴OFF | 🔴OFF | 🟢ON | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF |
| 3 | org_name3 | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF |

## 外部プラグインとの連携

### downloadモジュールを外部プラグインと連携

リソースがダウンロードされると、downloadモジュールはダウンロード数のカウント処理を行った後、デフォルトのダウンロードコールバックである`ckan.views.resource:download`を呼び出します。

しかし、そのコールバックを他Extensionの関数（例：[googleanalytics](https://github.com/ckan/ckanext-googleanalytics) のdownload関数）に変更したい場合は、`ckan.ini`の設定変数`ckan.feedback.download_handler`へ対象の関数を指定することで置き換えることが可能です。

**例**: **ckanext-feedback**で**ckanext-googleanalytics**のdownload関数を使用したい場合
```ini
ckan.feedback.download_handler = ckanext.googleanalytics.views:download
```

また、逆に外部ハンドラを設定できる他Extensionのコールバックとして**ckanext-feedback**のdownloadモジュールを指定したい場合は、`ckanext.feedback.views.download:download`を使用できます。

**例**: **ckanext-googleanalytics**で**ckanext-feedback**のdownload関数を使用したい場合
```ini
googleanalytics.download_handler = ckanext.feedback.views.download:download
```

> [!TIP]
> これらの連携方法は、複数のextensionを使用する際に`/download`などのパスが競合してしまう場合に役立ちます。
