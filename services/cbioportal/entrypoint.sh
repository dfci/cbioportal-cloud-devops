#!/usr/bin/env bash
PYTHON="/usr/bin/env python3"
MIGRATE_SCRIPT=${PORTAL_HOME}/core/src/main/scripts/migrate_db.py
PROPERTIES_FILE=${PORTAL_HOME}/src/main/resources/portal.properties
MIGRATION_SQL=${PORTAL_HOME}/db-scripts/src/main/resources/migration.sql
MIGRATION_COMMAND="${PYTHON} ${MIGRATE_SCRIPT} \
    --properties-file ${PROPERTIES_FILE} \
    --sql ${MIGRATION_SQL}"
RUN_CMD="/usr/local/tomcat/bin/catalina.sh run"

MYSQL_CONNECT_RETRIES=45
MYSQL_CONNECT_RETRY_COUNTER=1

echo "Attempting to connect to mysql://${DB_HOST}:${DB_PORT}"
while ! mysql -u"${DB_USER}" -p"${DB_PASSWORD}" -h"${DB_HOST}" -e "show databases;" > /dev/null 2>&1; do
    echo "Connection Attempt ${MYSQL_CONNECT_RETRY_COUNTER} failed"
    sleep 1
    MYSQL_CONNECT_RETRY_COUNTER=$(expr ${MYSQL_CONNECT_RETRY_COUNTER} + 1)
    if [ ${MYSQL_CONNECT_RETRY_COUNTER} -gt ${MYSQL_CONNECT_RETRIES} ]; then
        >&2 echo "We have been waiting for MySQL too long already; failing."
        exit 1
    fi;
done
echo "Connection Attempt ${MYSQL_CONNECT_RETRY_COUNTER} succeeded"

if ! mysqlshow -u"${DB_USER}" -p"${DB_PASSWORD}" -h"${DB_HOST}" ${DB_NAME}; then
    mysql -u"${DB_USER}" -p"${DB_PASSWORD}" -h"${DB_HOST}" -e "CREATE DATABASE ${DB_NAME};";
    mysql -u"${DB_USER}" -p"${DB_PASSWORD}" -h"${DB_HOST}" ${DB_NAME} < /root/schema.sql;
    zcat /root/seed-db.sql.gz | mysql -u"${DB_USER}" -p"${DB_PASSWORD}" -h"${DB_HOST}" ${DB_NAME};
    DATABASE_CREATED="yes"
fi

if [ "${DO_DB_MIGRATE}" == "yes" ] || [ "${DATABASE_CREATED}" == "yes" ]; then
    yes y | eval ${MIGRATION_COMMAND};
fi

eval ${RUN_CMD}