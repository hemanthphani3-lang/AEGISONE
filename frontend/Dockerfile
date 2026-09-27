# Stage 1: Build static assets
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Environment variables for build time (VITE_* embedded in bundle)
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_KEYCLOAK_URL=https://aegisone-keycloak.onrender.com
ARG VITE_KEYCLOAK_REALM=accessguard
ARG VITE_KEYCLOAK_CLIENT_ID=accessguard-frontend

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_KEYCLOAK_URL=$VITE_KEYCLOAK_URL
ENV VITE_KEYCLOAK_REALM=$VITE_KEYCLOAK_REALM
ENV VITE_KEYCLOAK_CLIENT_ID=$VITE_KEYCLOAK_CLIENT_ID

RUN npm run build

# Stage 2: Production Nginx Server
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
