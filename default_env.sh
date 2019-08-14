#!/usr/bin/env bash

export NGINX_WRAPPER_PORT_HTTP=80
export NGINX_WRAPPER_PORT_HTTPS=443
export CBIOPORTAL_BRANCH="v2.2.2"
export CBIOPORTAL_EXTERNAL_DATA="./mountpoints/cbioportal_external_data"
export CBIOPORTAL_SEED_SQL_FILE="seed-cbioportal_hg19_v2.7.3.sql.gz"
export CBIOPORTAL_IPV4_ADDR="172.28.10.11"
export CBIOPORTAL_MYSQL_IPV4_ADDR="172.28.10.12"
export ONCOKB_BRANCH="v1.0.7"
export GENOME_NEXUS_BRANCH="master"
export GENOME_NEXUS_MONGODB_BRANCH="master"
export SESSION_SERVICE_BRANCH="master"
export CANCERHOTSPOTS_BRANCH="master"
export SUBNET="172.28.10.0/24"
