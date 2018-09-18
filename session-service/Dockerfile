FROM openjdk:8-jdk
WORKDIR /root
RUN apt-get update
RUN apt-get install -y maven git
ARG BRANCH
RUN git clone https://github.com/cBioPortal/session-service.git --branch $BRANCH
RUN mvn -f session-service/pom.xml package -DskipTests -Dpackaging.type=jar
RUN mv session-service/target/session_service*.jar /session-service.jar
ENV SS_MONGO_HOST=session-service-mongodb SS_MONGO_PORT=27018 SS_MONGO_NAME=session-service SERVER_PORT=8090
ENTRYPOINT java -Dspring.data.mongodb.uri=mongodb://$SS_MONGO_HOST:$SS_MONGO_PORT/$SS_MONGO_NAME \
    -Dserver.port=$SERVER_PORT -Dserver.contextPath=/ -jar /session-service.jar
