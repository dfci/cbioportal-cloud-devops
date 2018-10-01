FROM mysql:5
RUN apt-get update && apt-get install -y curl
ARG BRANCH
RUN curl https://raw.githubusercontent.com/oncokb/oncokb/$BRANCH/core/src/main/resources/spring/database/oncokb.sql > \
    /docker-entrypoint-initdb.d/init.sql
