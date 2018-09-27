FROM tomcat:8
WORKDIR /root
RUN apt-get update && apt-get install -y git openjdk-8-jdk maven python3 python3-requests python3-jinja2 mysql-client

ARG BRANCH
ENV PORTAL_HOME=/root/cbioportal
RUN git clone https://github.com/cBioPortal/cbioportal.git --branch ${BRANCH} $PORTAL_HOME

ARG JDBC_DRIVER
ARG DB_HOST
ARG DB_PORT
ARG DB_USER
ARG DB_PASSWORD
ARG DB_NAME

COPY resources/* $PORTAL_HOME/src/main/resources/

RUN sed -i "s/@USERNAME_PLACEHOLDER@/$DB_USER/g" $PORTAL_HOME/src/main/resources/portal.properties &&  \
    sed -i "s/@PASSWORD_PLACEHOLDER@/$DB_PASSWORD/g" $PORTAL_HOME/src/main/resources/portal.properties &&  \
    sed -i "s/@HOST_PLACEHOLDER@/$DB_HOST/g" $PORTAL_HOME/src/main/resources/portal.properties &&  \
    sed -i "s/@PORT_PLACEHOLDER@/$DB_PORT/g" $PORTAL_HOME/src/main/resources/portal.properties &&  \
    sed -i "s/@DB_PLACEHOLDER@/$DB_NAME/g" $PORTAL_HOME/src/main/resources/portal.properties

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

COPY context.xml /usr/local/tomcat/conf/context.xml
RUN sed -i "s/@USERNAME_PLACEHOLDER@/$DB_USER/g" /usr/local/tomcat/conf/context.xml && \
    sed -i "s/@PASSWORD_PLACEHOLDER@/$DB_PASSWORD/g" /usr/local/tomcat/conf/context.xml && \
    sed -i "s/@HOST_PLACEHOLDER@/$DB_HOST/g" /usr/local/tomcat/conf/context.xml && \
    sed -i "s/@PORT_PLACEHOLDER@/$DB_PORT/g" /usr/local/tomcat/conf/context.xml && \
    sed -i "s/@DB_PLACEHOLDER@/$DB_NAME/g" /usr/local/tomcat/conf/context.xml
