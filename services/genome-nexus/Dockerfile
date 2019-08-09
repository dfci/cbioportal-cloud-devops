FROM openjdk:8-jdk
WORKDIR /root
RUN apt-get update && apt-get install -y maven git
ARG BRANCH
RUN git clone https://github.com/marriott-er/genome-nexus.git --branch $BRANCH
COPY application.properties genome-nexus/web/src/main/resources/application.properties
RUN mvn -f genome-nexus/pom.xml clean install -DskipTests && \
    mv genome-nexus/web/target/web*.war /app.war
ENV GN_MONGO_HOST=genome-nexus-mongodb GN_MONGO_PORT=27017 GN_MONGO_NAME=annotator
ENTRYPOINT java -Dspring.data.mongodb.uri=mongodb://$GN_MONGO_HOST:$GN_MONGO_PORT/$GN_MONGO_NAME -jar /app.war
