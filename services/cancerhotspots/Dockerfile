FROM openjdk:8-jdk
RUN apt-get update && apt-get -y install maven
WORKDIR /root
ARG BRANCH
RUN git clone https://github.com/cBioPortal/cancerhotspots.git --branch $BRANCH && \
    mvn -f cancerhotspots/pom.xml clean install -DskipTests
ENTRYPOINT java -jar cancerhotspots/webapp/target/cancerhotspots.jar
