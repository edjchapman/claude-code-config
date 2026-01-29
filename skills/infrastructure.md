---
name: infrastructure
description: Infrastructure as code patterns for Terraform, Kubernetes, and Helm.
globs:
  - "**/*.tf"
  - "**/k8s/**/*.yaml"
  - "**/k8s/**/*.yml"
  - "**/helm/**"
---

# Infrastructure Patterns

## Terraform

### Module Structure

- Use a standard layout: `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`
- Extract reusable patterns into modules under `modules/`
- Keep modules focused -- one resource group per module
- Use `terraform-docs` to auto-generate module documentation

### State Management

- Always use remote state (S3, GCS, or Terraform Cloud)
- Enable state locking (DynamoDB for S3 backend)
- Use separate state files per environment
- Never commit `.tfstate` files to version control
- Use `terraform import` for existing resources, never recreate

### Best Practices

- Pin provider versions in `versions.tf`
- Use `terraform fmt` and `terraform validate` in CI
- Run `terraform plan` in CI, apply only from CD pipeline
- Tag all resources with `environment`, `team`, and `managed_by`
- Use `data` sources to reference existing infrastructure
- Use `locals` for computed values, `variables` for inputs

## Kubernetes

### Resource Limits

- Always set `requests` and `limits` for CPU and memory
- `requests` = guaranteed minimum, `limits` = hard ceiling
- Start conservative and tune based on metrics
- Use `LimitRange` and `ResourceQuota` for namespace defaults

### Probes

- `livenessProbe`: restart if unhealthy (checks process is alive)
- `readinessProbe`: remove from service if not ready (checks dependencies)
- `startupProbe`: allow slow-starting containers before liveness kicks in
- Use HTTP probes for web services, TCP for databases, exec for custom checks
- Set `initialDelaySeconds` based on actual startup time

### Best Practices

- Use `Deployment` for stateless, `StatefulSet` for stateful workloads
- Define `PodDisruptionBudget` for high-availability services
- Use `ConfigMap` for config, `Secret` for sensitive data
- Set `imagePullPolicy: IfNotPresent` and use specific image tags
- Use namespaces to isolate environments and teams

## Helm

### Chart Best Practices

- Use `values.yaml` for defaults, override per environment
- Template helpers go in `_helpers.tpl`
- Include `NOTES.txt` for post-install instructions
- Use `helm lint` and `helm template` in CI
- Pin chart versions in `Chart.lock`
- Use subcharts for shared infrastructure (databases, caches)
