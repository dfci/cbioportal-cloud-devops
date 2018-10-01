FROM tomcat:8
WORKDIR /root
# necessary for building
RUN apt-get update && apt-get install -y git openjdk-8-jdk maven

ARG BRANCH
ENV PORTAL_HOME=/root/cbioportal JDBC_DRIVER=com.mysql.jdbc.Driver \
    DB_HOST=cbioportal-mysql DB_USER=root \
    DB_PASSWORD=letmein DB_PORT=3306 \
    DB_NAME=cbioportal

RUN git clone https://github.com/cBioPortal/cbioportal.git --branch ${BRANCH} $PORTAL_HOME

COPY resources/* $PORTAL_HOME/src/main/resources/

RUN mvn -f cbioportal/pom.xml -DskipTests -Djdbc.driver=$JDBC_DRIVER -Dfinal.war.name=cbioportal \
    -Ddb.host=$DB_HOST -Ddb.user=$DB_USER -Ddb.password=$DB_PASSWORD \
    -Ddb.connection_string=jdbc:mysql://$DB_HOST:$DB_PORT/ \
    -Ddb.portal_db_name=$DB_NAME clean install


RUN rm -rf /usr/local/tomcat/webapps/* && \
    mkdir -p /usr/local/tomcat/webapps/cbioportal && \
    unzip $PORTAL_HOME/portal/target/cbioportal.war -d /usr/local/tomcat/webapps/cbioportal && \
    cp -n $PORTAL_HOME/src/main/resources/* /usr/local/tomcat/webapps/cbioportal/WEB-INF/classes/ && \
    echo 'JAVA_OPTS="$JAVA_OPTS -Ddbconnector=dbcp"' >> /usr/local/tomcat/bin/setenv.sh && \
    chmod +x /usr/local/tomcat/bin/setenv.sh

#for running scripts and connecting to mysql in the container
RUN apt-get install -y python3-dev python3-requests python3-jinja2 \
        python3-setuptools mysql-client default-libmysqlclient-dev python3-pip && \
    pip3 install mysqlclient wget

RUN wget -O schema.sql \
     https://raw.githubusercontent.com/cBioPortal/cbioportal/v1.13.1/db-scripts/src/main/resources/cgds.sql && \
    wget -O seed-db.sql.gz \
     https://github.com/cBioPortal/datahub/raw/master/seedDB/seed-cbioportal_hg19_v2.6.0.sql.gz

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT /entrypoint.sh
