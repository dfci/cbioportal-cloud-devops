FROM tomcat:8
WORKDIR /root
# necessary for building
RUN apt-get update && apt-get install -y git openjdk-8-jdk maven

#for running scripts and connecting to mysql in the container
RUN apt-get install -y python3-dev python3-requests python3-jinja2 \
        python3-setuptools mysql-client default-libmysqlclient-dev python3-pip && \
    pip3 install mysqlclient wget

ENV PORTAL_HOME=/host/cbioportal JDBC_DRIVER=com.mysql.jdbc.Driver \
    DB_HOST=cbioportal-mysql DB_USER=root \
    DB_PASSWORD=letmein DB_PORT=3306 \
    DB_NAME=cbioportal BRANCH=master


RUN rm -rf /usr/local/tomcat/webapps/* && \
    echo 'JAVA_OPTS="$JAVA_OPTS -Ddbconnector=dbcp"' >> /usr/local/tomcat/bin/setenv.sh && \
    chmod +x /usr/local/tomcat/bin/setenv.sh

ARG BRANCH
RUN echo ${BRANCH} && \
    wget -O schema.sql \
     https://raw.githubusercontent.com/cBioPortal/cbioportal/${BRANCH}/db-scripts/src/main/resources/cgds.sql && \
    wget -O seed-db.sql.gz \
     https://github.com/cBioPortal/datahub/raw/master/seedDB/seed-cbioportal_hg19_v2.6.0.sql.gz

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT /entrypoint.sh
