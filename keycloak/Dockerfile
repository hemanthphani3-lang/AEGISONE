FROM quay.io/keycloak/keycloak:24.0.1 AS builder

# Build configuration options: single-node local cache, health, H2 dev-file DB
ENV KC_HEALTH_ENABLED=true
ENV KC_DB=dev-file
ENV KC_CACHE=local

COPY accessguard-realm.json /opt/keycloak/data/import/accessguard-realm.json

# Pre-compile Quarkus build optimization so runtime startup is instant & lightweight
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:24.0.1

COPY --from=builder /opt/keycloak/ /opt/keycloak/
COPY accessguard-realm.json /opt/keycloak/data/import/accessguard-realm.json

# Production environment defaults for single-instance Render deployment behind reverse proxy
ENV KC_HTTP_ENABLED=true
ENV KC_PROXY_HEADERS=xforwarded
ENV KC_HOSTNAME_STRICT=false
ENV KC_HEALTH_ENABLED=true
ENV KC_CACHE=local

# Tuned JVM memory settings for 512 MB RAM limit:
# - Heap: Min 64M, Max 192M
# - Metaspace: Max 160M
# - Thread Stacks: 512k (reduces thread stack footprint)
ENV JAVA_OPTS_KC_HEAP="-Xms64m -Xmx192m -XX:MaxMetaspaceSize=160m -Xss512k"

# Fast optimized startup with dynamic PORT binding for Render
ENTRYPOINT ["/bin/sh", "-c", "exec /opt/keycloak/bin/kc.sh start --optimized --import-realm --http-host=0.0.0.0 --http-port=${PORT:-8080}"]
