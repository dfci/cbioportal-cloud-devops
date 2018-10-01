# cBioPortal Cloud  Devops
This repo contains Dockerfiles and supporting files for getting a private instance of cBioPortal running with all external dependencies.

## Getting Started
### Project tree
 * [docker-compose.yml](./docker-compose.yml) - *Defines the network, services, and bind-mounts*
 * [scripts](./scripts)
     * [generate_self_signed_keys_for_nginx.sh](./scripts/generate_self_signed_keys_for_nginx.sh) - *Generates self-signed cert and key to use with nginx-wrapper, so you can test with HTTPS enabled, puts them in [./mountpoints/nginx-wrapper](./mountpoints/nginx-wrapper)*
 * [mountpoints](./mountpoints)
   * [cbioportal-mysql-data](./mountpoints/cbioportal-mysql-data) - *Directory that is bind-mounted to cbioportal-mysql to serve as the data directory*
   * [host](./mountpoints/host) - *Directory that is bind-mounted to /host on cbioportal and cbioportal-mysql, so files can be accessed on both easily if needed*
   * [nginx-wrapper](./mountpoints/nginx-wrapper) - *Directory to put cert.key and cert.crt for nginx-wrapper*
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

