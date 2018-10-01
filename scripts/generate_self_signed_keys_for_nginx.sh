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

openssl req -new -x509 -nodes -days 365 -newkey rsa:2048 -subj "/" \
    -keyout ${MAIN_PATH}/mountpoints/nginx-wrapper/cert.key \
    -out ${MAIN_PATH}/mountpoints/nginx-wrapper/cert.crt
