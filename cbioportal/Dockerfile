FROM debian:stretch
WORKDIR /root
RUN apt-get update && apt-get install -y locales
RUN locale-gen en_US.UTF-8
RUN apt-get install -y python3 python3-requests python3-yaml git openjdk-8-jdk maven


ARG BRANCH
ENV PORTAL_HOME=/root/cbioportal
RUN git clone https://github.com/cBioPortal/cbioportal.git --branch ${BRANCH} $PORTAL_HOME

ARG JDBC_DRIVER
ARG DB_HOST
ARG DB_PORT
ARG DB_USER
ARG DB_PASSWORD
ARG DB_NAME
COPY portal.properties $PORTAL_HOME/src/main/resources/portal.properties
RUN mvn -f cbioportal/pom.xml -DskipTests -Djdbc.driver=$JDBC_DRIVER -Dfinal.war.name=cbioportal \
    -Ddb.host=$DB_HOST -Ddb.user=$DB_USER -Ddb.password=$DB_PASSWORD \
    -Ddb.connection_string=jdbc:mysql://$DB_HOST:$DB_PORT/ \
    -Ddb.portal_db_name=$DB_NAME -Dtomcat.catalina.scope=runtime clean install
RUN env
CMD ["/bin/bash", "-c", "java -Ddbconnector=dbcp -jar $PORTAL_HOME/portal/target/dependency/webapp-runner.jar --expand-war $PORTAL_HOME/portal/target/cbioportal.war"]
