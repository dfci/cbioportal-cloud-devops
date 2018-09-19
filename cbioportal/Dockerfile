FROM tomcat:8
WORKDIR /root
RUN apt-get update
RUN apt-get install -y git openjdk-8-jdk maven
RUN rm -rf /usr/local/tomcat/webapps/*


ARG BRANCH
ENV PORTAL_HOME=/root/cbioportal
RUN git clone https://github.com/cBioPortal/cbioportal.git --branch ${BRANCH} $PORTAL_HOME

ARG JDBC_DRIVER
ARG DB_HOST
ARG DB_PORT
ARG DB_USER
ARG DB_PASSWORD
ARG DB_NAME


RUN mvn -f cbioportal/pom.xml -DskipTests -Djdbc.driver=$JDBC_DRIVER -Dfinal.war.name=cbioportal \
    -Ddb.host=$DB_HOST -Ddb.user=$DB_USER -Ddb.password=$DB_PASSWORD \
    -Ddb.connection_string=jdbc:mysql://$DB_HOST:$DB_PORT/ \
    -Ddb.portal_db_name=$DB_NAME -Dtomcat.catalina.scope=runtime clean install

COPY portal.properties $PORTAL_HOME/src/main/resources/portal.properties
COPY context.xml /usr/local/tomcat/conf/context.xml

RUN sed -i "s/@USERNAME_PLACEHOLDER@/$DB_USER/g" /usr/local/tomcat/conf/context.xml
RUN sed -i "s/@PASSWORD_PLACEHOLDER@/$DB_PASSWORD/g" /usr/local/tomcat/conf/context.xml
RUN sed -i "s/@HOST_PLACEHOLDER@/$DB_HOST/g" /usr/local/tomcat/conf/context.xml
RUN sed -i "s/@PORT_PLACEHOLDER@/$DB_PORT/g" /usr/local/tomcat/conf/context.xml
RUN sed -i "s/@DB_PLACEHOLDER@/$DB_NAME/g" /usr/local/tomcat/conf/context.xml

RUN ln -s $PORTAL_HOME/portal/target/cbioportal.war /usr/local/tomcat/webapps/cbioportal.war
