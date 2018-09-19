FROM mysql:5
RUN apt-get update
RUN apt-get install -y curl
ARG BRANCH
RUN curl https://raw.githubusercontent.com/oncokb/oncokb/$BRANCH/core/src/main/resources/spring/database/oncokb.sql > /init.sql
ENTRYPOINT bash -c "(if [[ ! -f /init_done ]]; then \
    sleep 5;\
    mysql --password=$MYSQL_ROOT_PASSWORD $MYSQL_DATABASE --host=127.0.0.1 < /init.sql;\
    touch /init_done; \
    fi) & \
    /entrypoint.sh mysqld"
