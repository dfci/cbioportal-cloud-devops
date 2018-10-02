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

echo "Commencing test verification"
${HOME}/.acme.sh/acme.sh --test --issue -d ${DOMAIN} --dns dns_gcloud

echo "Does everything look OK?  To continue, in uppercase with no quotes, type \"yes\"."
read ACMERESPONSE
if [ ${ACMERESPONSE} == "YES" ]; then
    rm -rf ${HOME}/.acme.sh/${DOMAIN}
    ${HOME}/.acme.sh/acme.sh --issue -d ${DOMAIN} --dns dns_gcloud
    echo "Will now stop nginx-wrapper and install cert. To continue, in uppercase with no quotes, type \"yes\"."
    read NGINXRESPONSE
    if [ ${NGINXRESPONSE} == "YES" ]; then
        docker-compose -f ${MAIN_PATH}/docker-compose.yml stop nginx-wrapper
        rm ${MAIN_PATH}/mountpoints/nginx-wrapper/cert.key
        rm ${MAIN_PATH}/mountpoints/nginx-wrapper/cert.crt
        ln -s ${HOME}/.acme.sh/${DOMAIN}/${DOMAIN}.key ${MAIN_PATH}/mountpoints/nginx-wrapper/cert.key
        ln -s ${HOME}/.acme.sh/${DOMAIN}/${DOMAIN}.cer ${MAIN_PATH}/mountpoints/nginx-wrapper/cert.crt
        docker-compose -f ${MAIN_PATH}/docker-compose.yml up -d --no-deps --build nginx-wrapper
    fi
fi

