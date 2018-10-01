#!/usr/bin/env bash
MAIN_PATH=$(dirname $(dirname $(readlink -f "$0")))
yes | openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
 -keyout ${MAIN_PATH}/services/nginx-wrapper/cert.key \
 -out ${MAIN_PATH}/services/nginx-wrapper/cert.crt
