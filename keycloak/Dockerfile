FROM quay.io/keycloak/keycloak:24.0.1 AS builder

# Build configuration options
ENV KC_HEALTH_ENABLED=true
ENV KC_HTTP_RELATIVE_PATH=/
ENV KC_DB=dev-file

COPY accessguard-realm.json /opt/keycloak/data/import/accessguard-realm.json

# Pre-compile Quarkus build optimization so runtime startup is instant & lightweight
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:24.0.1

COPY --from=builder /opt/keycloak/ /opt/keycloak/
COPY accessguard-realm.json /opt/keycloak/data/import/accessguard-realm.json

# Production environment defaults for Render reverse proxy
ENV KC_HTTP_ENABLED=true
ENV KC_HTTP_HOST=0.0.0.0
ENV KC_HTTP_PORT=8080
ENV KC_PROXY_HEADERS=xforwarded
ENV KC_HOSTNAME_STRICT=false
ENV KC_HEALTH_ENABLED=true

# Tuned JVM memory settings for 512 MB RAM limit:
# - Heap: Min 64M, Max 192M
# - Metaspace: Max 160M (Keycloak class loading requires ~128MB-160MB Metaspace)
ENV JAVA_OPTS_KC_HEAP="-Xms64m -Xmx192m -XX:MaxMetaspaceSize=160m"

# Fast optimized startup with dynamic PORT binding for Render
ENTRYPOINT ["/bin/sh", "-c", "export KC_HTTP_PORT=${PORT:-${KC_HTTP_PORT:-8080}} && exec /opt/keycloak/bin/kc.sh start --optimized --import-realm"]
