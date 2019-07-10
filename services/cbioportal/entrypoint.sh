#!/usr/bin/env bash
PYTHON="/usr/bin/env python3"
MIGRATE_SCRIPT=${PORTAL_HOME}/core/src/main/scripts/migrate_db.py
PROPERTIES_FILE=${PORTAL_HOME}/src/main/resources/portal.properties
MIGRATION_SQL=${PORTAL_HOME}/db-scripts/src/main/resources/migration.sql
MIGRATION_COMMAND="${PYTHON} ${MIGRATE_SCRIPT} \
    --properties-file ${PROPERTIES_FILE} \
    --sql ${MIGRATION_SQL}"
RUN_CMD="/usr/local/tomcat/bin/catalina.sh run"

MYSQL_CONNECT_RETRIES=120
MYSQL_CONNECT_RETRY_COUNTER=1

if [ ! -d ${PORTAL_HOME} ]; then
    git clone https://github.com/cBioPortal/cbioportal.git --branch ${BRANCH} ${PORTAL_HOME}
fi

cp /resources/* ${PORTAL_HOME}/src/main/resources/

if [ "${FORCE_MVN_BUILD}" == "yes" ] || [ ! -d /usr/local/tomcat/webapps/${SUBPATH} ]; then
    cd ${PORTAL_HOME}
    rm -rf /usr/local/tomcat/webapps/${SUBPATH}/*
    mvn -f ${PORTAL_HOME}/pom.xml -DskipTests -Djdbc.driver=${JDBC_DRIVER} -Dfinal.war.name=cbioportal \
        -Ddb.host=${DB_HOST} -Ddb.user=${DB_USER} -Ddb.password=${DB_PASSWORD} \
        -Ddb.connection_string=jdbc:mysql://${DB_HOST}:${DB_PORT}/ \
        -Ddb.portal_db_name=${DB_NAME} ${MVN_GOALS};
    echo "Exploding cbioportal.war to webapps ${SUBPATH} directory";
    unzip ${PORTAL_HOME}/portal/target/cbioportal.war -d /usr/local/tomcat/webapps/${SUBPATH} > /dev/null 2>&1;
fi;

echo "Copying uncopied resources to classpath"
cp -n ${PORTAL_HOME}/src/main/resources/* /usr/local/tomcat/webapps/${SUBPATH}/WEB-INF/classes/ > /dev/null 2>&1

echo "Attempting to connect to mysql://${DB_HOST}:${DB_PORT}"
while ! mysql -u"${DB_USER}" -p"${DB_PASSWORD}" -h"${DB_HOST}" -e "show databases;" > /dev/null 2>&1; do
    echo "Connection Attempt ${MYSQL_CONNECT_RETRY_COUNTER} of ${MYSQL_CONNECT_RETRIES} failed"
    sleep 1
    MYSQL_CONNECT_RETRY_COUNTER=$(expr ${MYSQL_CONNECT_RETRY_COUNTER} + 1)
    if [ ${MYSQL_CONNECT_RETRY_COUNTER} -gt ${MYSQL_CONNECT_RETRIES} ]; then
        >&2 echo "We have been waiting for MySQL too long already; failing."
        exit 1
    fi;
done
echo "Connection Attempt ${MYSQL_CONNECT_RETRY_COUNTER} succeeded"

echo "Checking for existence of database ${DB_NAME}";
if ! mysqlshow -u"${DB_USER}" -p"${DB_PASSWORD}" -h"${DB_HOST}" ${DB_NAME} > /dev/null 2>&1; then
    echo "Database ${DB_NAME} does not exist, creating";
    mysql -u"${DB_USER}" -p"${DB_PASSWORD}" -h"${DB_HOST}" -e "CREATE DATABASE ${DB_NAME};";
    mysql -u"${DB_USER}" -p"${DB_PASSWORD}" -h"${DB_HOST}" ${DB_NAME} < /root/schema.sql;
    zcat /root/seed-db.sql.gz | mysql -u"${DB_USER}" -p"${DB_PASSWORD}" -h"${DB_HOST}" ${DB_NAME};
    DATABASE_CREATED="yes"
else
    echo "Database ${DB_NAME} exists"
fi

if [ "${DO_DB_MIGRATE}" == "yes" ] || [ "${DATABASE_CREATED}" == "yes" ]; then
    echo "Running database migration script";
    yes y | eval ${MIGRATION_COMMAND};
fi

eval ${RUN_CMD}
