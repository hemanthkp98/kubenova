# syntax=docker/dockerfile:1
# KubeNova Frontend — Multi-stage Dockerfile
# Stage 1: builder — install dependencies and build the Vite/React app
# Stage 2: runtime — nginx serving the static files with API proxy

# ---- builder ----
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies.
COPY package.json package-lock.json* ./
RUN npm ci --silent

# Copy source and build.
COPY . .
RUN npm run build

# ---- runtime ----
FROM nginx:alpine AS runtime

# Copy the built app.
COPY --from=builder /app/dist /usr/share/nginx/html

# Custom nginx configuration for SPA + API proxy.
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD wget -q --spider http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
