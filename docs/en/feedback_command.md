# ckan feedback init

Initialize PostgreSQL tables related to the specified feature.

## Execution

```bash
ckan feedback init [options]
```

### Options

#### -m, --modules < utilization/ resource/ download >

Optional

* Specify one or more of the following three options if you want to use some features. (Multiple selections allowed)  
* If this option is not specified, initialization will be performed on all tables.
  * utilization
  * resource
  * download

##### Example (--module option)

```bash
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

* When executing the ckan command, you need to specify the config file by writing ```--config=/etc/ckan/production.ini```.

#### -h, --host <host_name>

Optional

* Specify the host name of the PostgreSQL container.  
* If not specified, the following values will be used in order.
  * Environment variable ```POSTGRES_HOST```
  * CKAN default value ```db```

#### -p, --port <port>

Optional

* Specify the port number of the PostgreSQL container.  
* If not specified, the following values will be used in order.
  * Environment variable ```POSTGRES_PORT```
  * CKAN default value ```5432```

#### -d, --dbname <db_name>

Optional

* Specify the name of the PostgreSQL database.  
* If not specified, the following values will be used in order.
  * Environment variable ```POSTGRES_DB```
  * CKAN default value ```ckan```

#### -u, --user <user_name>

Optional

* Specify the username to connect to PostgreSQL.  
* If not specified, the following values will be used in order.
  * Environment variable ```POSTGRES_USER```
  * CKAN default value ```ckan```

#### -P, --password <password>

Optional

* Specify the password to connect to PostgreSQL.  
* If not specified, the following values will be used in order.
  * Environment variable ```POSTGRES_PASSWORD```
  * CKAN default value ```ckan```

##### Example (Other options)

```bash
# Specify "postgresdb" as the host name
ckan --config=/etc/ckan/production.ini feedback init -h postgresdb

# Specify "5000" as the port number
ckan --config=/etc/ckan/production.ini feedback init -p 5000

# Specify "ckandb" as the database name
ckan --config=/etc/ckan/production.ini feedback init -d ckandb

# Specify "root" as the username
ckan --config=/etc/ckan/production.ini feedback init -u root

# Specify "root" as the password
ckan --config=/etc/ckan/production.ini feedback init -P root

# Specify "postgresdb" as the host name, "root" as the username, and "root" as the password
ckan --config=/etc/ckan/production.ini feedback init -h postgresdb -u root -P root
```
