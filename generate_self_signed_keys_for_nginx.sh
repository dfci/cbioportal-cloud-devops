#!/usr/bin/env bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout ./nginx-wrapper/cert.key -out ./nginx-wrapper/cert.crt
