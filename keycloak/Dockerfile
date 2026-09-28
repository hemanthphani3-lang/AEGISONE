FROM quay.io/keycloak/keycloak:24.0.1 AS builder

# Build configuration options: single-node local cache, health, H2 dev-file DB
ENV KC_HEALTH_ENABLED=true
ENV KC_DB=dev-file
ENV KC_CACHE=local

COPY accessguard-realm.json /opt/keycloak/data/import/accessguard-realm.json

# Pre-compile Quarkus build optimization
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:24.0.1

COPY --from=builder /opt/keycloak/ /opt/keycloak/
COPY accessguard-realm.json /opt/keycloak/data/import/accessguard-realm.json

# Render reverse proxy configuration
ENV KC_HTTP_ENABLED=true
ENV KC_PROXY_HEADERS=xforwarded
ENV KC_HOSTNAME_STRICT=false
ENV KC_HEALTH_ENABLED=true

# Single-node cache; prevents unnecessary JGroups clustering
ENV KC_CACHE=local

# JVM memory tuning for Render 512 MiB instance
ENV JAVA_OPTS_KC_HEAP="-Xms64m -Xmx192m -XX:MaxMetaspaceSize=160m -Xss512k"

# Render dynamically provides PORT
ENTRYPOINT ["/bin/sh", "-c", "exec /opt/keycloak/bin/kc.sh start --optimized --import-realm --http-host=0.0.0.0 --http-port=${PORT:-8080}"]

