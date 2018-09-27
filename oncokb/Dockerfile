FROM tomcat:8
WORKDIR /root
RUN apt-get update && apt-get -y install openjdk-8-jdk git maven
ARG BRANCH
RUN git clone https://github.com/oncokb/oncokb.git --branch $BRANCH && \
    mkdir -p oncokb/core/src/main/resources/properties && \
    echo 'cancerhotspots.website.link=http://cancerhotspots.org' >> oncokb/core/src/main/resources/properties/config.properties && \
    echo 'cancerhotspots.single=http://cancerhotspots:28080/api/hotspots/single' >> oncokb/core/src/main/resources/properties/config.properties && \
    mvn -f oncokb/pom.xml clean install -P backend -pl web,core -DskipTests && \
    rm -rf /usr/local/tomcat/webapps/* && \
    cp oncokb/web/target/oncokb.war /usr/local/tomcat/webapps/oncokb.war
ARG DB_HOST
ARG DB_PORT
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ENV JAVA_OPTS="-Djdbc.driverClassName=com.mysql.jdbc.Driver -Djdbc.url='jdbc:mysql://'$DB_HOST':'$DB_PORT'/oncokb?useUnicode=yes&characterEncoding=UTF-8' -Djdbc.username=$DB_USER -Djdbc.password=$DB_PASSWORD"
