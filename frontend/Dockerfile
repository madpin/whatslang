# syntax=docker/dockerfile:1.7

FROM node:20-alpine AS builder

# Ensure qemu exposes the CPU features Node expects when cross-building arm64.
ENV QEMU_CPU=max

WORKDIR /app

# Install dependencies using cached npm directory; layer only changes when package lock changes
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copy application source
COPY . .

# Build assets
RUN CI=true npm run build:prod

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

