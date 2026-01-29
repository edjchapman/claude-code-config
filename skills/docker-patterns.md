---
name: docker-patterns
description: Docker best practices including multi-stage builds, layer caching, security, and compose patterns.
globs:
  - "**/Dockerfile"
  - "**/docker-compose*.yml"
  - "**/.dockerignore"
---

# Docker Patterns

## Multi-Stage Builds

- Use multi-stage builds to separate build dependencies from runtime
- Name stages for clarity: `FROM node:20 AS builder`
- Copy only build artifacts into the final stage
- Keep the final image as small as possible (use `slim` or `alpine` base images)

## Layer Caching

- Order instructions from least to most frequently changing
- Copy dependency files (`package.json`, `requirements.txt`) before source code
- Group related `RUN` commands with `&&` to reduce layers
- Use `.dockerignore` to exclude unnecessary files from build context

## .dockerignore

- Always include: `.git`, `node_modules`, `__pycache__`, `.env`, `*.log`
- Mirror `.gitignore` patterns plus build artifacts
- Exclude test files and documentation from production images

## Security

- Never run as root -- use `USER nonroot` or create a dedicated user
- Don't store secrets in images -- use environment variables or secrets managers
- Pin base image versions: `python:3.12-slim` not `python:latest`
- Scan images for vulnerabilities with `docker scout` or `trivy`
- Use `COPY` instead of `ADD` unless you need tar extraction

## Health Checks

- Always define `HEALTHCHECK` in production Dockerfiles
- Use lightweight endpoints (`/healthz`) that check actual dependencies
- Set appropriate intervals, timeouts, and retries
- Health checks should complete quickly (< 5s)

## Compose Best Practices

- Use named volumes for persistent data
- Define explicit networks for service isolation
- Use `depends_on` with health check conditions
- Use `.env` files for environment configuration
- Define resource limits (`mem_limit`, `cpus`) for production
- Use `profiles` to group services by environment (dev, test, prod)
