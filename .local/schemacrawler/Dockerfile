FROM eclipse-temurin:21-jre

ARG SC_VERSION=17.6.2

RUN apt-get update && apt-get install -y unzip curl graphviz && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN curl -L -o schemacrawler.zip \
    https://github.com/schemacrawler/SchemaCrawler/releases/download/v${SC_VERSION}/schemacrawler-${SC_VERSION}-distribution.zip \
    && unzip schemacrawler.zip \
    && mv schemacrawler-${SC_VERSION}-distribution/_schemacrawler schemacrawler \
    && rm -rf schemacrawler-${SC_VERSION}-distribution \
    && rm schemacrawler.zip

WORKDIR /work

ENTRYPOINT ["/opt/schemacrawler/bin/schemacrawler.sh"]