# cBioPortal Cloud  Devops
This repo contains Dockerfiles and supporting files for getting a private instance of cBioPortal running with all external dependencies.

## Getting Started
## Project tree
 * [docker-compose.yml](./docker-compose.yml) - *Defines the network, services, and bind-mounts*
 * [scripts](./scripts)
     * [generate_self_signed_keys_for_nginx.sh](./scripts/generate_self_signed_keys_for_nginx.sh) - *Generates self-signed cert and key to use with nginx-wrapper, so you can test with HTTPS enabled, puts them in [./mountpoints/nginx-wrapper](./mountpoints/nginx-wrapper)*
     * [gce_debian_9_setup.sh](./scripts/gce_debian_9_setup.sh) - *Setup script for Debian image in Google Cloud*
     * [letsencrypt_gcloud.sh](./scripts/letsencrypt_gcloud.sh) - *Helper script to issue SSL certs from LetsEncrypt on Google Cloud*
 * [mountpoints](./mountpoints)
   * [cbioportal-mysql-data](./mountpoints/cbioportal-mysql-data) - *Directory that is bind-mounted to cbioportal-mysql to serve as the data directory*
   * [host](./mountpoints/host) - *Directory that is bind-mounted to /host on cbioportal and cbioportal-mysql, so files can be accessed on both easily if needed*
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

## Prerequisites
All that is needed is docker-compose >= 1.12.0 and docker >= 17.04.0.
To generate a self-signed cert, openssl is needed.

## Instructions
This assumes that you have shell access to the environment you will be using, either as the root user, or as a user who is a member of the docker group.

The instructions will be using a Debian GNU/Linux 9 (stretch) VM on Google Compute Engine, but the instructions should be more or less the same on any \*nix system that meets the prerequisites.

### Step 0 - Creating a VM on GCE with proper storage and volumes
Skip this step if you already have an environment.  Following steps will assume you already have the repo cloned.

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
4. If there is a DNS record for the server and you wish to have valid CA certs for the server, you can run ```./scripts/letsencrypt_gcloud.sh /path/to/service_worker_authorization.json```, where serivce_worker_authorization.json is an authorization file from google for a service worker with Cloud DNS admin privileges, and follow the prompts.  Otherwise, run [./scripts/generate_self_signed_keys_for_nginx.sh](./scripts/generate_self_signed_keys_for_nginx.sh) to generate a self-signed cert and key for nginx.


