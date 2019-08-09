FROM maven:3.5.4
USER root
WORKDIR /
RUN apt-get update && apt-get install -y git
ARG BRANCH
RUN git clone --branch $BRANCH --depth=1 https://github.com/genome-nexus/genome-nexus-vep.git && \
    cd genome-nexus-vep && \
    mvn -DskipTests clean install
FROM ensemblorg/ensembl-vep:release_92.1
USER root
RUN apt-get update && apt-get -y install openjdk-8-jre
COPY --from=0 /genome-nexus-vep/target/vep_wrapper*.jar /opt/vep/src/ensembl-vep/vep_wrapper.jar

USER vep
WORKDIR /opt/vep/src/ensembl-vep/
ENTRYPOINT exec java ${JAVA_OPTS} -jar vep_wrapper.jar

