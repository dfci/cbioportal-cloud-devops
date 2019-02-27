# cBioPortal Cloud  Devops
This repo contains Dockerfiles and supporting files for getting a private instance of cBioPortal running with all external dependencies.

## Prerequisites
All that is needed is docker-compose >= 1.12.0 and docker >= 17.04.0.
To generate a self-signed cert, openssl is needed.

## Instructions
This assumes that you have shell access to the environment you will be using, either as the root user, or as a user who is a member of the docker group.

The instructions will be using a Debian GNU/Linux 9 (stretch) VM on Google Compute Engine, but the instructions should be more or less the same on any \*nix system that meets the prerequisites.

### Creating a VM on GCE with proper storage and volumes
Skip this section if you already have an environment.  Following steps will assume you already have the repo cloned.

1. Create a new VM instance on GCE
    - Debian GNU/Linux (stretch) 9
    - Boot Dist: SSD Persistent Disk, 24GB (should be bigger than the default 10GB just because we'll have lots of intermediate container images)
    - Firewall: Allow HTTP and HTTPS traffic
    - Disks: 1x blank 32GB+ SSD Persistent Disk, R/W (for the cbioportal-mysql data)
2. SSH into the new instance, switch to root user (no point in doing it all through sudo on single-purpose system), install git, and clone the repo
    ```
    emarriott@cbiorportal-cloud-edenstate-2:~$ sudo su
    root@cbiorportal-cloud-edenstate-2:~# apt-get update && apt-get install git
    root@cbiorportal-cloud-edenstate-2:~# cd
    root@cbiorportal-cloud-edenstate-2:~# git clone git@github.com:dfci/cbioportal-cloud-devops.git
    root@cbiorportal-cloud-edenstate-2:~# cd cbioportal-cloud-devops/
    ```

3. Run the script scripts/gce_debian_9_setup.sh
4. If there is a DNS record for the server and you wish to have valid CA certs for the server, you can run ```./scripts/letsencrypt_gcloud.sh /path/to/service_worker_authorization.json```, where service_worker_authorization.json is an authorization file from google for a service worker with Cloud DNS admin privileges, and follow the prompts.  Otherwise, run [./scripts/generate_self_signed_keys_for_nginx.sh](./scripts/generate_self_signed_keys_for_nginx.sh) to generate a self-signed cert and key for nginx.

### Steps
1. Make sure you have cloned this repo, and have a shell open in the directory (cbioportal-cloud-devops)
2. If you wish to store the cbioportal mysql data on a separate block device, make sure it is mounted to [./mountpoints/cbioportal-mysql-data](./mountpoints/cbioportal-mysql-data)
    - Using a bind mount: ```mount  -o bind /path/to/location/to/store/data ./mountpoints/cbioportal-mysql-data```
    - Mounting the block device directly ```mount /dev/devicename ./mountpoints/cbioportal-mysql-data```
3. Make any required changes to the portal.properties file in [./services/cbioportal/resources/portal.properties](./services/cbioportal/resources/portal.properties)
4. Make sure any other resources that may be required for your instance of cBioPortal, such as a SAML keystore, are placed in [./services/cbioportal/resources](./services/cbioportal/resources)
5. Run ```source default_env.sh``` to load the necessary environment variables to run the docker-compose, or source your own custom environment file.
6. Run ```docker-compose build``` to build the images
7. Make sure all required and desired environment variables are set (see [Environment Variables](#environment-variables))
8. Run ```docker-compose up -d``` to start cbioportal and all associated services
9. View the logs by running ```docker-compose logs -f```
10. On first run, cbioportal will clone the cbioportal repository to ```/host/cbioportal```. ```/host``` is bind-mounted from [./mountpoints/host](./mountpoints/host).  If you wish to force cbioportal to reclone the repo, just run ```rm -rf ./mountpoints/host/cbioportal```
11. Also on first run, cbioportal will build the project.  On subsequent runs, if you wish to rebuild, run the container with the environment variable FORCE_MVN_BUILD=yes, e.g. ```FORCE_MVN_BUILD=yes docker-compose up -d```
12. On startup, cbioportal will wait until it can get a connection to cbioportal-mysql, and check for the cbioportal database.  If the database does not exist, it will be created, and populated with the seed data.
13. Also on startup, if the database was created, or if the environment variable DO_DB_MIGRATE is set to "yes" (without quotes), the database migration script will be run.  This means you can force the migration script to run when bringing the container up, e.g. ```DO_DB_MIGRATE=yes docker-compose up -d```
    - To force the a build of cbioportal as well as force db migrate script to be run, do ```FORCE_MVN_BUILD=yes DO_DB_MIGRATE=yes docker-compose up -d```
14. Studies will be loaded by the import-pipeline every night by default every night, for details or to make modifications check [services/import-pipeline/import_service/main.py](./services/import-pipeline/import_service/main.py).  Studies automatically imported via the import-pipeline will show up in the dashboard at <your-url>/dashboard, where you can check study versions validation and import status.
15. To load studies without going through the import-pipeline, put whatever files/folders you need into [./mountpoints/host](./mountpoints/host), where they will be accessible in the cbioportal container under ```/host```.  You can get shell access to the cbioportal container by running ```docker-compose exec cbioportal bash```.
    - ```${PORTAL_HOME}``` is set to ```/host/cbioportal```, so you can load studies and run all scripts like you would normally.

## Useful Commands
- Stop a single service, e.g. cbioportal
    - ```docker-compose stop cbioportal```
- Bring up a single service, e.g. cbioportal
    - ```docker-compose up -d --no-deps cbioportal```
- Bring up a single service and recreate it if already running, e.g. cbioportal
    - ```docker-compose up -d --no-deps --force-recreate cbioportal```
- Start cbioportal, forcing build
    - ```FORCE_MVN_BUILD=yes docker-compose up -d --no-deps cbioportal```
- Start cbioportal, forcing db migrate script to run
    - ```DO_DB_MIGRATE=yes docker-compose up -d --no-deps cbioportal```
- Start cbioportal, forcing build, and running the db migrate script 
    - ```FORCE_MVN_BUILD=yes DO_DB_MIGRATE=yes docker-compose up -d --no-deps cbioportal```
- Get a shell in cbioportal container
    - ```docker-compose exec cbioportal bash```
- Get a mysql prompt to cbioportal-mysql
    - ```docker-compose exec cbioportal-mysql mysql -pletmein cbioportal```
    
## Environment Variables
- General Variables (not associated with any service in particular)
    - SUBNET
        - CIDR IPV4 subnet for the Docker network
        - Default: "172.28.10.0/24"
- import-pipeline
    - ACCESS_TOKEN
        - Dropbox API access token
        - Default: [not set by default]
    - ALLOWED_FOLDER
        - Comma-separated list of top-level folders containing studies in Dropbox
        - Default: [not set by default]
    - ADMIN_EMAILS
        - Comma-separated list of emails that should have access to all studies in cBioPortal
        - Default: [not set by default]
    - GCLOUD_CREDS
        - Contents of the Google Compute Cloud credentials JSON file for accessing the Google sheet with user information
        - Default: [not set by default]
    - AUTH_SHEET_KEY
        - The spreadsheet ID of the Google sheet with user information
        - Default: [not set by default]
    - AUTH_SHEET_WORKSHEET_NAME
        - The title of the worksheet in the Google sheet
        - Default: [not set by default]
    - AUTH_SHEET_KEYMAP
        - JSON mapping the required fields of the USERS table to headers of the columns in the Google sheet
        - e.g. export AUTH_SHEET_KEYMAP='{"name": ["First Name", "Last Name"], "email": "Email address", "enabled": "Approved by whomever"}'

        - If the value of "name" is a list of column headers, the values at each of those columns will be joined by a space
        - Default: [not set by default]
    - AUTH_SHEET_TRUEVAL
        - The string in the spreadsheet denoting a TRUE value
        - e.g. "Yes"
        - Default: [not set by default]
- cbioportal
    - DO_DB_MIGRATE
        - If this is set to "yes", then the container will attempt to run the DB migration script on start
        - Default: "no"
    - FORCE_MVN_BUILD
        - If this is set to "yes", then the container will build cBioPortal on start
        - Even if this is not set, if /usr/local/tomcat/webapps/ROOT does not exist, the project will still be built
        - Default: "no"
    - CBIOPORTAL_BRANCH
        - Branch (of public cBioPortal repo) to clone/build cBioPortal from
        - Default: "v2.0.1"
    - CBIOPORTAL_SEED_SQL_FILE
        - Filename of the seed database to use, from the public cBioPortal DataHub
        - Default: "seed-cbioportal_hg19_v2.7.2.sql.gz"
    - CBIOPORTAL_IPV4_ADDR
        - IPV4 address to run cBioPortal on, must be within the ${SUBNET} specified
        - Default: "172.28.10.11"
- cbioportal-mysql
    - CBIOPORTAL_MYSQL_IPV4_ADDR
        - IPV4 address to run cBioPortal MySQL database on, must be withing the ${SUBNET} specified
        - Default: "172.28.10.12"
- oncokb
    - ONCOKB_BRANCH
        - Branch to clone/build OncoKB from
        - Default: "v0.3.11"
- genome-nexus
    - GENOME_NEXUS_BRANCH
        - Branch to clone/build Genome Nexus from
        - Default: "master"
- genome-nexus-mongodb
    - GENOME_NEXUS_MONGODB_BRANCH
        - Branch to clone/build the Genome Nexus Importer from
        - Default: "v0.8"
- session-service
    - SESSION_SERVICE_BRANCH
        - Branch to clone/build the session-service from
        - Default: "master"
- cancerhotspots
    - CANCERHOTSPOTS_BRANCH
        - Branch to clone/build cancerhotspots from
        - Default: "master"
        
## Project tree
 * [docker-compose.yml](./docker-compose.yml) - *Defines the network, services, and bind-mounts*
 * [scripts](./scripts)
     * [generate_self_signed_keys_for_nginx.sh](./scripts/generate_self_signed_keys_for_nginx.sh) - *Generates self-signed cert and key to use with nginx-wrapper, so you can test with HTTPS enabled, puts them in [./mountpoints/nginx-wrapper](./mountpoints/nginx-wrapper)*
     * [gce_debian_9_setup.sh](./scripts/gce_debian_9_setup.sh) - *Setup script for Debian image in Google Cloud*
     * [letsencrypt_gcloud.sh](./scripts/letsencrypt_gcloud.sh) - *Helper script to issue SSL certs from LetsEncrypt on Google Cloud*
 * [mountpoints](./mountpoints)
   * [cbioportal-mysql-data](./mountpoints/cbioportal-mysql-data) - *Directory that is bind-mounted to cbioportal-mysql to serve as the data directory*
   * [dashboard](./mountpoints/dashboard) - *Directory that is bind-mounted to import-pipeline to put dashboard data and also bind-mounted to nginx-wrapper to host the dashboard at /dashboard*
     * [index.html](./mountpoints/dashboard/index.html) - *HTML for the import-pipeline dashboard*
     * [main.css](./mountpoints/dashboard/main.css) - *CSS for the import-pipeline dashboard*
     * [main.js](./mountpoints/dashboard/main.js) - *JS for the import-pipeline dashboard*
   * [host](./mountpoints/host) - *Directory that is bind-mounted to /host on cbioportal and cbioportal-mysql, so files can be accessed on both easily if needed*
   * [importer](./mountpoints/importer) - *Directory that is bind-mounted to import-pipeline to serve as the data directory; files downloaded from dropbox are stored here, as well as the sqlite3 database to maintain state*
   * [nginx-wrapper](./mountpoints/nginx-wrapper) - *Directory to put cert.key and cert.crt for nginx-wrapper*
   * [mvn-repo](./mountpoints/mvn-repo) - *Directory that is bind-mounted to /root/.m2/repository on the cbioportal container, to cache maven dependencies*
 * [services](./services) - *One folder for each service, containing the Dockerfile and supporting files*
   * [nginx-wrapper](./services/nginx-wrapper) - *Only service that binds to host ports, proxies traffic to cbioportal*
     * [Dockerfile](./services/nginx-wrapper/Dockerfile)
     * [nginx.conf](./services/nginx-wrapper/nginx.conf) - *Config file for nginx, attaced to container as a bind-mount, there should be no reason to change this except to modify routing behavior*
   * [cbioportal](./services/cbioportal)
     * [context.xml](./services/cbioportal/context.xml) - *context.xml for tomcat, attached as a bind-mount - there should be no reason to change this*
     * [Dockerfile](./services/cbioportal/Dockerfile)
     * [entrypoint.sh](./services/cbioportal/entrypoint.sh) - *Copied to the container at build time, overrides the default entrypoint to run the migration script on startup*
     * [resources](./services/cbioportal/resources) - *Contents of this folder are copied to the container at build time, before the maven build step, to ${PORTAL_HOME}/src/main/resources*
       * [portal.properties](./services/cbioportal/resources/portal.properties) - *portal.properties file for configuring your instance of cBioPortal.  As with everything else in this directory, it is copied to the container at build time. This is the most likely file for you to need change*
   * [cbioportal-mysql](./services/cbioportal-mysql) - *MySQL backend for cBioPortal, data is stored in a directory bind-mounted to the container at runtime, [./mountpoints/cbioportal-mysql-data](./mountpoints/cbioportal-mysql-data)*
     * [custom.cnf](./services/cbioportal-mysql/custom.cnf) - *bind-mounted to the container at runtime for performance tuning, feel free to modify this based on the specs of the machine you're running the container on*
     * [Dockerfile](./services/cbioportal-mysql/Dockerfile)
   * [session-service](./services/session-service) - *session-service for cBioPortal*
     * [Dockerfile](./services/session-service/Dockerfile)
   * [session-service-mongodb](./services/session-service-mongodb) - *MongoDB backend for session-service*
     * [Dockerfile](./services/session-service-mongodb/Dockerfile)
   * [genome-nexus](./services/genome-nexus) - *Genome Nexus service for cBioPortal*
     * [Dockerfile](./services/genome-nexus/Dockerfile)
   * [genome-nexus-mongodb](./services/genome-nexus-mongodb) - *MongoDB backend for Genome Nexus*
     * [Dockerfile](./services/genome-nexus-mongodb/Dockerfile)
   * [oncokb](./services/oncokb) - *OncoKB service for cBioPortal*
     * [Dockerfile](./services/oncokb/Dockerfile)
   * [oncokb-mysql](./services/oncokb-mysql) - *MySQL backend for OncoKB*
     * [Dockerfile](./services/oncokb-mysql/Dockerfile)
   * [cancerhotspots](./services/cancerhotspots) - *Cancer Hotspots service for OncoKB, making it a secondary requirement for cBioPortal*
     * [Dockerfile](./services/cancerhotspots/Dockerfile)
   * [import-pipeline](./services/import-pipeline) - *Import Pipeline for loading, validating, and keeping track of studies in DropBox*
     * [Dockerfile](./services/import-pipeline/Dockerfile)
     * [schema.sql](./services/import-pipeline/schema.sql) - *schema for the sqlite3 database that maintains study versions state*
     * [import_service](./services/import-pipeline/import_service/) - *Python package for making up the import-pipeline*
        * [\_\_init\_\_.py](./services/import-pipeline/import_service/__init__.py)
        * [main.py](./services/import-pipeline/import_service/main.py) - *Main script for import-pipeline - uses imports all other modules, and sets of scheduling for different services*
        * [FileSyncSource.py](./services/import-pipeline/import_service/FileSyncSource.py) - *Module for interacting with DropBox*
        * [StudyManageMentAccess.py](./services/import-pipeline/import_service/StudyManagementAccess.py) - *Module which handles authorization on studies, and user management from a Google sheet*
        * [StudyManagementItemAccess.py](./services/import-pipeline/import_service/StudyManagementItemAccess.py) - *Module for interacting with the sqlite3 db for reading, writing and tracking study state*
        * [StudyManagementItems.py](./services/import-pipeline/import_service/StudyManagementItems.py) - *Module which represents the data structures stored in the sqlite3 database, allowing read/write access*
        * [StudySync.py](./services/import-pipeline/import_service/StudySync.py) - *Module containing the actual services for study importing/validation/downloading/versioning*
        * [Util.py](./services/import-pipeline/import_service/Util.py) - *Module containing various utilities, functions, abstractions, etc.*
