# ckan feedback init

## Overview

Initialize PostgreSQL tables related to the specified feature.

## Execution

```
ckan feedback init [options]
```

### Options

#### -m, --modules < utilization/ resource/ download >

**Optional**

Specify and execute from the following three options when using some features. (Multiple selections allowed)  
If this option is not specified, initialization will be performed for all tables.
* utilization
* resource
* download

##### Execution Examples

```
# Initialize all tables related to ckanext-feedback plugins
ckan --config=/etc/ckan/production.ini feedback init

# Initialize tables related to the utilization feature
ckan --config=/etc/ckan/production.ini feedback init -m utilization

# Initialize tables related to the resource feature
ckan --config=/etc/ckan/production.ini feedback init -m resource

# Initialize tables related to the download feature
ckan --config=/etc/ckan/production.ini feedback init -m download

# Initialize tables related to both the resource and download features
ckan --config=/etc/ckan/production.ini feedback init -m resource -m download
```

※ When executing the ckan command, you need to specify the config file by writing ```--config=/etc/ckan/production.ini```.

#### -h, --host <host_name>

**Optional**

Specify the hostname of the PostgreSQL container.  
If not specified, the value will be referenced in the following order.
1. Environment variable ```POSTGRES_HOST```
2. CKAN default value ```db```

#### -p, --port <port>

**Optional**

Specify the port number of the PostgreSQL container.  
If not specified, the value will be referenced in the following order.
1. Environment variable ```POSTGRES_PORT```
2. CKAN default value ```5432```

#### -d, --dbname <db_name>

**Optional**

Specify the name of the PostgreSQL database.  
If not specified, the value will be referenced in the following order.
1. Environment variable ```POSTGRES_DB```
2. CKAN default value ```ckan```

#### -u, --user <user_name>

**Optional**

Specify the username to connect to PostgreSQL.  
If not specified, the value will be referenced in the following order.
1. Environment variable ```POSTGRES_USER```
2. CKAN default value ```ckan```

#### -P, --password <password>

**Optional**

Specify the password to connect to PostgreSQL.  
If not specified, the value will be referenced in the following order.
1. Environment variable ```POSTGRES_PASSWORD```
2. CKAN default value ```ckan```

##### Execution Examples

```
# Specify "postgresdb" as the hostname
ckan --config=/etc/ckan/production.ini feedback init -h postgresdb

# Specify "5000" as the port number
ckan --config=/etc/ckan/production.ini feedback init -p 5000

# Specify "ckandb" as the database name
ckan --config=/etc/ckan/production.ini feedback init -d ckandb

# Specify "root" as the username
ckan --config=/etc/ckan/production.ini feedback init -u root

# Specify "root" as the password
ckan --config=/etc/ckan/production.ini feedback init -P root

# Specify "postgresdb" as the hostname, "root" as the username, and "root" as the password
ckan --config=/etc/ckan/production.ini feedback init -h postgresdb -u root -P root
```

## Database Update Method

For information on how to update the schema without initializing the database, please refer to the following document.</br>
- [db_migration.md](../../docs/ja/db_migration.md)