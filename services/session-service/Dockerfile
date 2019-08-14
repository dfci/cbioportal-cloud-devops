FROM openjdk:8-jdk
WORKDIR /root
RUN apt-get update && apt-get install -y maven git
ARG BRANCH
RUN git clone https://github.com/cBioPortal/session-service.git --branch $BRANCH && \
    mvn -f session-service/pom.xml package -DskipTests -Dpackaging.type=jar && \
    ls /root/session-service/target/session_service* && \
    mv /root/session-service/target/session_service*model.jar /session-service.jar
ENV SS_MONGO_HOST=session-service-mongodb SS_MONGO_PORT=27017 SS_MONGO_NAME=session-service SERVER_PORT=8090
ENTRYPOINT java -Dspring.data.mongodb.uri=mongodb://$SS_MONGO_HOST:$SS_MONGO_PORT/$SS_MONGO_NAME \
    -Dserver.port=$SERVER_PORT -Dserver.contextPath=/ -jar /session-service.jar
