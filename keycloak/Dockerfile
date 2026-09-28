# Stage 1: Compile lightweight static reverse proxy & process supervisor
FROM golang:1.22-alpine AS proxy-builder
WORKDIR /app
COPY entrypoint-proxy.go .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o entrypoint-proxy entrypoint-proxy.go

# Stage 2: Pre-compile Keycloak Quarkus build optimizations
FROM quay.io/keycloak/keycloak:24.0.1 AS keycloak-builder

ENV KC_HEALTH_ENABLED=true
ENV KC_DB=dev-file
ENV KC_CACHE=local

COPY accessguard-realm.json /opt/keycloak/data/import/accessguard-realm.json

RUN /opt/keycloak/bin/kc.sh build

# Stage 3: Production Runtime Image
FROM quay.io/keycloak/keycloak:24.0.1

COPY --from=proxy-builder /app/entrypoint-proxy /opt/keycloak/bin/entrypoint-proxy
COPY --from=keycloak-builder /opt/keycloak/ /opt/keycloak/
COPY accessguard-realm.json /opt/keycloak/data/import/accessguard-realm.json

# Production environment defaults for single-instance Render deployment behind reverse proxy
ENV KC_HTTP_ENABLED=true
ENV KC_PROXY_HEADERS=xforwarded
ENV KC_HOSTNAME_STRICT=false

# JVM memory and CPU tuning for 512 MB Render instance:
# - Heap: Min 64M, Max 192M
# - Metaspace: Max 160M
# - JIT: TieredStopAtLevel=1 (C1 JIT compiler reduces CPU compilation overhead on shared cloud CPUs)
# - Thread Stacks: 512k (reduces native stack footprint)
ENV JAVA_OPTS_KC_HEAP="-Xms64m -Xmx192m -XX:MaxMetaspaceSize=160m -XX:TieredStopAtLevel=1 -Xss512k"

# Process supervisor immediately binds 0.0.0.0:$PORT for Render port scanner
ENTRYPOINT ["/opt/keycloak/bin/entrypoint-proxy"]
