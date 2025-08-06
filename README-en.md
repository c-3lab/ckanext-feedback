English | [日本語](https://github.com/c-3lab/ckanext-feedback/blob/main/README.md)

# ckanext-feedback

[![codecov](https://codecov.io/github/c-3lab/ckanext-feedback/graph/badge.svg?token=8T2RIXPXOM)](https://codecov.io/github/c-3lab/ckanext-feedback)

This CKAN Extension provides functionality to obtain feedback from data users.  
The mechanism for receiving opinions/requests and reports on usage examples from users of this extension will help data users understand data and promote data utilization, while data providers will be able to understand data needs and improve the data improvement process. You can improve efficiency.

Feedback enables an ecosystem between users and providers that continually improves the data.

## Main features

* 👀 Visualization function for aggregate information (number of downloads, number of uses, number of problems solved)
* 💬 Comment and evaluation function for data and usage methods
* 🖼 Feature to introduce apps and systems that utilize data
* 🏆 Problem-solving certification function for apps and systems that utilize data

## Quick Start

Below are the steps to apply this extension to an existing CKAN environment.

### Prerequisites

* We assume that CKAN 2.10.4 is installed in the following environment, and that this extension will be added to it:
  * OS: Linux
  * Distribution: Ubuntu 22.04
  * Python 3.10.13

### Steps

1. Install `ckanext-feedback` in your CKAN environment.

    * If you are running CKAN in a virtual environment (e.g., venv), please activate it before executing the command.

    ```bash
    pip install ckanext-feedback
    ```

2. Open the CKAN configuration file (`ckan.ini`) with the following command:

    * Specify the path where `ckan.ini` is located.
    * If you are unsure about the path, you can search for it by running `find / -name ckan.ini`.

    ```bash
    vim /etc/ckan/ckan.ini
    ```

3. Add `feedback` to the following line:

    ```bash
    ckan.plugins = stats ・・・ recline_view feedback
    ```

4. Create the necessary tables for the feedback functionality:

    ```bash
    ckan db upgrade -p feedback
    ```
    * If you encounter an error such as `ckan.ini` not found, run `ckan -c <path to ckan.ini> db upgrade -p feedback` instead.

## Structure

### Three modules that make up this extension

* [utilization](./docs/ja/utilization.md)
* [resource](./docs/ja/resource.md)
* [download](./docs/ja/download.md)

### Documentation related to configuration and management

* You can manage comments on resources and ways of utilizing data.
  * For details, see the [Administrator Screen Documentation](docs/ja/admin.md).

* It is also possible to use only specific modules.
  * See [Detailed Documentation on Switching Features](./docs/ja/switch_function.md) for the configuration.

* The actions that can be performed vary depending on whether the user is logged in and on the user's privileges (e.g., admin).
  * For details on permissions, see the [Detailed Documentation on Administrator Privileges](./docs/ja/authority.md).

## For Developers

Here are the steps for developing this extension in a Docker environment.

### Prerequisites

* We assume that CKAN and this extension will be run in the following Docker environment:
  * OS: Linux
  * Distribution: Ubuntu 22.04
  * Python 3.10.13
  * Docker 27.4.0

### Build Procedure

1. Clone `ckanext-feedback` from GitHub to your local environment:

    ```bash
    git clone https://github.com/c-3lab/ckanext-feedback.git
    ```

2. Move to the `ckanext-feedback/development` directory and run `container_setup.sh` to start the container.

3. While in the same `ckanext-feedback/development` directory, run `feedback_setup.sh` to install `ckanext-feedback` and create the necessary tables.

    * During `feedback_setup.sh` execution, you may see a message like `The feedback config file not found`, but this is not an issue.
    * The file `feedback_config.json` is referred to as `The feedback config file` and is explained in the [Detailed Documentation on Switching Features](./docs/ja/switch_function.md).

4. Access `http://localhost:5000`.

### Development Preparation

#### Installing Packages with Poetry
When developing this extension, please use Poetry to install the required packages.
1. Install `poetry`:

    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    ```

2. Move to the project root directory, where the `pyproject.toml` file is located, and install the required packages:

    ```bash
    poetry install
    ```

### Linter and Formatter Settings
Enable the Linter and Formatter:

```bash
poetry run pre-commit install
```

* From now on, whenever you run `git commit`, `isort`, `black`, and `pflake8` will automatically run on the staged files. If they make any changes, the commit will be aborted.
* To run `isort`, `black`, and `pflake8` manually, you can run `poetry run pre-commit`.

### Reference Documentation

* [Detailed Documentation of the `feedback` Command](./docs/ja/feedback_command.md)
* [Detailed Documentation on Language Support (i18n)](./docs/ja/i18n.md)

### Testing

1. Build the environment following the steps above.

2. Enter the container:

    ```bash
    docker exec -it --user root ckan-docker-ckan-dev-1 /bin/bash
    ```

3. Install any additional requirements:

    ```bash
    pip install -r /srv/app/src/ckan/dev-requirements.txt
    pip install pytest-ckan
    ```

4. Move to the following directory:

    ```bash
    cd /usr/lib/python3.10/site-packages/ckanext/feedback/tests
    ```

5. Execute tests:

    ```bash
    CKAN_SQLALCHEMY_URL= CKAN_DATASTORE_READ_URL= CKAN_DATASTORE_WRITE_URL= pytest -s --ckan-ini=config/test.ini --cov=ckanext.feedback --cov-branch --disable-warnings --cov-config=/srv/app/src_extensions/ckanext-feedback/.coveragerc ./
    ```

## LICENSE

[AGPLv3 LICENSE](https://github.com/c-3lab/ckanext-feedback/blob/feature/documentation-README/LICENSE)

## CopyRight

Copyright (c) 2023 C3Lab

