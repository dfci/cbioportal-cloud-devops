FROM mongo:3.6.2
RUN apt-get update && apt-get install -y git
ARG BRANCH
ENV REF_ENSEMBL_VERSION="grch37_ensembl92"
RUN git clone --branch $BRANCH --depth=1 https://github.com/genome-nexus/genome-nexus-importer.git && \
    mkdir -p /data/ && \
    mv genome-nexus-importer/data/* /data/ && \
    rm -rf /data/*/input /data/*/tmp && \
    mv genome-nexus-importer/scripts/import_mongo.sh /docker-entrypoint-initdb.d/
