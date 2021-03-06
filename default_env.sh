#!/usr/bin/env bash

export NGINX_WRAPPER_PORT_HTTP=80
export NGINX_WRAPPER_PORT_HTTPS=443
export CBIOPORTAL_BRANCH="v2.0.1"
export CBIOPORTAL_EXTERNAL_DATA="./mountpoints/cbioportal_external_data"
export CBIOPORTAL_SEED_SQL_FILE="seed-cbioportal_hg19_v2.7.2.sql.gz"
export CBIOPORTAL_IPV4_ADDR="172.28.10.11"
export CBIOPORTAL_MYSQL_IPV4_ADDR="172.28.10.12"
export ONCOKB_BRANCH="v0.3.11"
export GENOME_NEXUS_BRANCH="master"
export GENOME_NEXUS_MONGODB_BRANCH="v0.8"
export SESSION_SERVICE_BRANCH="master"
export CANCERHOTSPOTS_BRANCH="master"
export SUBNET="172.28.10.0/24"
