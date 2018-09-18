FROM tomcat:8
WORKDIR /root
RUN apt-get update
RUN apt-get -y install openjdk-8-jdk git maven mysql-client
ARG BRANCH
RUN git clone https://github.com/oncokb/oncokb.git --branch $BRANCH
RUN mvn -f oncokb/pom.xml clean install -P backend -pl web,core -DskipTests
RUN rm -rf /usr/local/tomcat/webapps/*
RUN cp oncokb/web/target/oncokb.war /usr/local/tomcat/webapps/oncokb.war
ARG DB_HOST
ARG DB_PORT
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
RUN mysql --user=$DB_USER --password=$DB_PASSWORD --host=$DB_HOST --port=$DB_PORT -e 'DROP DATABASE IF EXISTS '${DB_NAME}';'
RUN mysql --user=$DB_USER --password=$DB_PASSWORD --host=$DB_HOST --port=$DB_PORT -e 'CREATE DATABASE '${DB_NAME}';'
RUN mysql --user=$DB_USER --password=$DB_PASSWORD --host=$DB_HOST --port=$DB_PORT $DB_NAME < \
    oncokb/core/src/main/resources/spring/database/oncokb.sql
ENV JAVA_OPTS="-Djdbc.driverClassName=com.mysql.jdbc.Driver -Djdbc.url='jdbc:mysql://'$DB_HOST':'$DB_PORT'/oncokb?useUnicode=yes&characterEncoding=UTF-8' -Djdbc.username=$DB_USER -Djdbc.password=$DB_PASSWORD"
