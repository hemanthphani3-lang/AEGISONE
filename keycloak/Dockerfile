# Use official Keycloak 24.0.1 image compatible with existing project setup
FROM quay.io/keycloak/keycloak:24.0.1

# Copy existing AegisOne realm configuration for automatic startup import
COPY accessguard-realm.json /opt/keycloak/data/import/accessguard-realm.json

# Default environment configuration for production operation behind reverse proxy (Render)
ENV KC_HTTP_ENABLED=true
ENV KC_PROXY_HEADERS=xforwarded
ENV KC_HTTP_PORT=8080

# Start Keycloak in production mode importing accessguard-realm.json, dynamic PORT support for Render
ENTRYPOINT ["/bin/sh", "-c", "export KC_HTTP_PORT=${PORT:-${KC_HTTP_PORT:-8080}} && exec /opt/keycloak/bin/kc.sh start --import-realm"]
