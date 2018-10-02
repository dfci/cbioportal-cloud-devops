#!/usr/bin/env bash
# readlink -f shim in case not using GNU readlink
readlink_f () {
    TARGET_FILE=$1
    cd $(dirname ${TARGET_FILE})
    TARGET_FILE=$(basename ${TARGET_FILE})
    while [ -L "${TARGET_FILE}" ]
    do
        TARGET_FILE=$(readlink ${TARGET_FILE})
        cd $(dirname ${TARGET_FILE})
        TARGET_FILE=$(basename ${TARGET_FILE})
    done
    PHYS_DIR=`pwd -P`
    RESULT=${PHYS_DIR}/${TARGET_FILE}
    echo ${RESULT}
}

MAIN_PATH=$(dirname $(dirname $(readlink_f "$0")))

gcloud auth activate-service-account --key-file "$1"

curl https://get.acme.sh | sh
echo "Please enter the domain name of this server, e.g. example.com"
read DOMAIN
. ${HOME}/.acme.sh/acme.sh.env
acme.sh --test --issue -d ${DOMAIN} -d *.cbiodfci.org --dns dns_gcloud
