# ckanext-feedback Command List

Provides dedicated CLI commands for operation and maintenance purposes.  
You can flexibly perform initialization, maintenance, and cleanup of data related to feedback features.  

> [!IMPORTANT]
> The `ckan` command must be executed where `ckan.ini` is located, or the `ckan.ini` path must be specified with `-c`.


## Table of Contents

- [init](#init)
  - [Execution](#execution)
  - [Options](#options)
  - [Execution Examples](#execution-examples)
- [clean-files](#clean-files)
  - [Execution](#execution-1)
  - [Options](#options-1)
  - [Execution Examples](#execution-examples-1)
  - [Supplement: Criteria for Determining Deletion Targets](#supplement-criteria-for-determining-deletion-targets)

## init

Initializes PostgreSQL tables related to specified features.  
The target of initialization can be controlled with options, and if not specified, all tables will be targeted.

### Execution

```bash
ckan ckan.ini feedback init [options]
```

### Options

```bash
-m, --modules < utilization resource download >
```

Execute initialization processing limited to target features (optional)

No specification: Execute initialization processing for all tables  
Module specification: Multiple module names can be specified from the following:
- utilization
- resource
- download

```bash
-h, --host <host_name>
```

Specify PostgreSQL hostname (optional)

Priority order:  
1. Command line argument  
2. Environment variable POSTGRES_HOST  
3. CKAN default: db

```bash
-p, --port <port>
```

Specify PostgreSQL port number (optional)

Priority order:  
1. Command line argument  
2. Environment variable POSTGRES_PORT  
3. CKAN default: 5432

```bash
-d, --dbname <db_name>
```

Specify PostgreSQL database name (optional)

Priority order:  
1. Command line argument  
2. Environment variable POSTGRES_DB  
3. CKAN default: ckan

```bash
-u, --user <user_name>
```

Specify PostgreSQL connection username (optional)

Priority order:  
1. Command line argument  
2. Environment variable POSTGRES_USER  
3. CKAN default: ckan

```bash
-P, --password <password>
```

Specify PostgreSQL connection password (optional)

Priority order:  
1. Command line argument  
2. Environment variable POSTGRES_PASSWORD  
3. CKAN default: ckan

### Execution Examples

```bash
# Initialize all tables related to ckanext-feedback plugins
ckan ckan.ini feedback init

# Initialize tables related to the utilization feature
ckan ckan.ini feedback init -m utilization

# Initialize tables related to the resource feature
ckan ckan.ini feedback init -m resource

# Initialize tables related to the download feature
ckan ckan.ini feedback init -m download

# Initialize tables related to both resource and download features
ckan ckan.ini feedback init -m resource -m download

# Specify "postgresdb" as hostname
ckan ckan.ini feedback init -h postgresdb

# Specify "5000" as port number
ckan ckan.ini feedback init -p 5000

# Specify "ckandb" as database name
ckan ckan.ini feedback init -d ckandb

# Specify "root" as username
ckan ckan.ini feedback init -u root

# Specify "root" as password
ckan ckan.ini feedback init -P root

# Specify "postgresdb" as hostname, "root" as username, and "root" as password
ckan ckan.ini feedback init -h postgresdb -u root -P root
```

## clean-files

Searches for and deletes unnecessary image files that were uploaded during comment submission but were not actually attached to comments.  
Files that were temporarily uploaded during feedback submission but remained without completing the submission are targeted.

### Execution

```bash
ckan ckan.ini feedback clean-files [options]
```

### Options

```bash
-d, --dry-run
```

Displays a list of files to be deleted without actually deleting them.  
Useful when you want to check the scope of impact before execution.

### Execution Examples

```bash
# Delete unnecessary files
ckan ckan.ini feedback clean-files

# Display a list of files to be deleted without actually deleting them
ckan ckan.ini feedback clean-files --dry-run
```

### Supplement: Criteria for Determining Deletion Targets

- Files **not associated** with completed comment submissions
- **Orphaned image files** temporarily saved on the server

※ We recommend checking in advance with `--dry-run` to avoid unintentionally deleting files.  
※ We recommend running this command regularly with cron or similar.

