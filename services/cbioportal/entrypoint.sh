#!/usr/bin/env bash
PYTHON="/usr/bin/env python3"
MIGRATE_SCRIPT=${PORTAL_HOME}/core/src/main/scripts/migrate_db.py
PROPERTIES_FILE=${PORTAL_HOME}/src/main/resources/portal.properties
MIGRATION_SQL=${PORTAL_HOME}/db-scripts/src/main/resources/migration.sql
MIGRATION_COMMAND="${PYTHON} ${MIGRATE_SCRIPT} \
    --properties-file ${PROPERTIES_FILE} \
    --sql ${MIGRATION_SQL}"
RUN_CMD="/usr/local/tomcat/bin/catalina.sh run"

if [ ! -z "${DO_DB_MIGRATE}" ]; then
    yes y | eval ${MIGRATION_COMMAND};
fi

eval ${RUN_CMD}