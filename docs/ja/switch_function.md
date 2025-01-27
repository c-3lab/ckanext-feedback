# ON/OFF 機能

本ドキュメントでは、**ckanext-feedback**のモジュールと機能に関するON/OFFについて説明します。

**ckanext-feedback**は既にインストール済みであることを前提としています。  
まだインストールが完了していない場合は、[README](../../README.md)に記載の**クイックスタート**に従い、インストールを完了させてください。

## 機能説明

- **ckanext-feedback**で追加された以下のモジュールや機能のON/OFFを切り替えることができます。
  - [utilization](./utilization.md)   
  データの利活用方法に関するモジュール  
  デフォルト：🟢**ON**

  - [resource](./resource.md)  
  リソースへのコメントに関するモジュール  
  デフォルト：🟢**ON**

  - [repeat post limit](./resource.md)  
  1つのリソースに対してコメントできる回数を各ユーザーごと、1回に制限する機能  
  デフォルト：🔴**OFF**

  - [rating](./resource.md)  
  リソースへの評価を行う機能  
  デフォルト：🔴**OFF**

  - [download](./download.md)  
  ダウンロードに関するモジュール  
  デフォルト：🟢**ON**

  ※ [repeat post limit](./resource.md)と[rating](./resource.md)に関しては、[resource](./resource.md)が🟢**ON**になっている場合にのみON/OFFを切り替えることができます。

## 設定方法

- 各モジュールと機能のON/OFFを設定するには、以下の２通りの方法があります。
  - `ckan.ini`にON/OFFの設定を記述する。
  - `feedback_config.json`に設定を記述し、CKAN環境に配置する。  
  ※ 組織毎の設定を行いたい場合は、`feedback_config.json`でのみ設定することができます。

### 設定優先度

`ckan.ini`に本設定がされていても、`feedback_config.json`がサーバー内に存在する場合は、`feedback_config.json`の内容をもとに設定が反映されます。

（例）  
`ckan.ini`でモジュールや機能を🔴**OFF**に設定  
`feedback_config.json`でモジュールや機能を🟢**ON**に設定  
→ モジュールや機能は🟢**ON**になります。  
(※ この動作は、以下の相互作用の5番に該当します。)

詳細は以下の**相互作用**、 **ユースケース別設定適用表**を参照してください。  

### 相互作用

モジュールや機能のON/OFF設定が、`ckan.ini`と`feedback_config.json`のそれぞれに記述された値によってどのように決定されるかを示しています。

- **ckan.ini**：`ckan.ini`に記述したモジュールや機能のenable設定値です。
- **feedback_config.json**：`feedback_config.json`に記述したモジュールや機能のenable設定値です。
- **ON/OFF**：モジュールや機能のON/OFF設定の結果です。

| No. | ckan.ini | feedback_config.json | ON/OFF |
| :-: | :-: | :-: | :-: |
| 1 | - | - | デフォルト値 |
| 2 | ✔️True | - | 🟢ON |
| 3 | - | ✔️True | 🟢ON |
| 4 | ✔️True | ✔️True | 🟢ON |
| 5 | ❌False | ✔️True | 🟢ON |
| 6 | ❌False | - | 🔴OFF |
| 7 | - | ❌False | 🔴OFF |
| 8 | ✔️True | ❌False | 🔴OFF |
| 9 | ❌False | ❌False | 🔴OFF |

### ユースケース別設定適用表

`feedback_config.json`を用いて設定する際、特定のユースケース毎にモジュールや機能のON/OFF設定をどのように適用するかを示しています。

- **enable**：`feedback_config.json`に記述したモジュールや機能のenable設定値です。
- **enable_orgs**：`feedback_config.json`に記述したモジュールや機能を🟢ONにしたい組織の名前リストです。
- **disable_orgs**：`feedback_config.json`に記述したモジュールや機能を🔴OFFにしたい組織の名前リストです。

| No. | ユースケース | enable | enable_orgs | disable_orgs |
| :-: | :-: | :-: | :-: | :-: |
| 1 | 全ての組織でモジュールや機能を🟢ONにしたい場合 | ✔️True | - | - |
| 2 | 全ての組織でモジュールや機能を🔴OFFにしたい場合 | ❌False | - | - |
| 3 | 組織毎に🟢ON/🔴OFFを設定したい場合 | ✔️True | ["org_name1", "org_name2"] | ["org_name3"] |
| 4 | 特定の組織のみ🔴OFFにしたい場合 | ✔️True | - | ["org_name3"] |

※ **enable_orgs**と**disable_orgs**に同じ組織を記載した場合、設定は不適切であり、該当する組織のモジュールや機能は🔴**OFF**になります。  

（例）  
```json
{
    "enable_orgs": ["org_name1", "org_name2"],
    "disable_orgs": ["org_name1", "org_name3"]
}
```  
→ **"org_name1"** の設定は🔴**OFF**になる

## 設定例

### `ckan.ini`でON/OFFの設定を行う

※ この方法で設定を行った場合はすべての組織のモジュールや機能は🟢ONまたは、🔴OFFになります。  
※ `feedback_config.json`がCKAN環境に配置されている場合は本設定は反映されません。

（例）すべてのモジュールや機能を🟢ONにする場合
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
| No. | 組織名 | utilization | resource | repeated_post_limit | rating | download |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | org_name1 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 2 | org_name2 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 3 | org_name3 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |

### `feedback_config.json`でON/OFFの設定を行う

（例）すべてのモジュールや機能を🟢ONにする場合
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
| No. | 組織名 | utilization | resource | repeated_post_limit | rating | download |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | org_name1 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 2 | org_name2 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 3 | org_name3 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |

（例）組織毎にモジュールや機能のON/OFFを設定する場合
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
| No. | 組織名 | utilization | resource | repeated_post_limit | rating | download |
| :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| 1 | org_name1 | 🟢ON | 🟢ON | 🟢ON | 🟢ON | 🟢ON |
| 2 | org_name2 | 🟢ON | 🟢ON | 🔴OFF | 🔴OFF | 🟢ON |
| 3 | org_name3 | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF | 🔴OFF |

## downloadモジュールを外部プラグインと連携

リソースがダウンロードされると、downloadモジュールはダウンロード数のカウント処理を行った後、デフォルトのダウンロードコールバックである`ckan.views.resource:download`を呼び出します。  
しかし、そのコールバックを他Extensionの関数（例：[googleanalytics](https://github.com/ckan/ckanext-googleanalytics) のdonwload関数）に変更したい場合は、`ckan.ini`の設定変数`ckan.feedback.download_handler`へ対象の関数を指定することで置き換えることが可能です。  

（例）**ckanext-feedback**で**ckanext-googleanalytics**のdonwload関数を使用したい場合
  ```bash
  ckan.feedback.download_handler = ckanext.googleanalytics.views:download
  ```

また、逆に外部ハンドラを設定できる他Extensionのコールバックとして**ckanext-feedback**のdownloadモジュールを指定したい場合は、`ckanext.feedback.views.download:download`を使用できます。  

（例）**ckanext-googleanalytics**で**ckanext-feedback**のdonwload関数を使用したい場合  
  ```bash
  googleanalytics.download_handler = ckanext.feedback.views.download:download
  ```

これらの連携方法は、複数のextensionを使用する際に`/download`などのパスが競合してしまう場合に役立ちます。
