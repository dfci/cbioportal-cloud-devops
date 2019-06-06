FROM mongo:3
RUN apt-get update && apt-get install -y git
ARG BRANCH
RUN git clone --branch $BRANCH --depth=1 https://github.com/genome-nexus/genome-nexus-importer.git && \
    mkdir -p /export/ && \
    mv genome-nexus-importer/export/* /export/ && \
    mv genome-nexus-importer/scripts/import_mongo.sh /docker-entrypoint-initdb.d/
