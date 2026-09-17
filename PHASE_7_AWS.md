# Phase 7 — AWS production hardening

```text
                         Internet
                            │
                            ▼
                    ALB :443 / HTTPS
                            │
                       private ECS
                    ┌───────┴───────┐
                    │               │
                  FastAPI         FastAPI
                    │               │
             ┌──────┴───────┐       │
             ▼              ▼       │
        RDS PostgreSQL   Redis TLS  │
             │              │       │
             └──────┬───────┘       │
                    ▼               ▼
                 CloudWatch / Metrics / Alarms
```

## Implemented

- Private ECS Fargate tasks.
- Public ALB.
- HTTPS listener + HTTP→HTTPS redirect.
- ACM certificate input.
- RDS PostgreSQL Multi-AZ.
- Redis TLS + failover.
- ECR immutable SHA tags + lifecycle cleanup.
- Secrets Manager.
- ECS deployment circuit breaker with rollback.
- ECS CPU target tracking autoscaling.
- CloudWatch alarms for ALB 5xx, ECS CPU and running task count.
- GitHub Actions OIDC restricted to `main`.
- GitHub deployment role with ECR/ECS/PassRole permissions.
- CI tests before deployment.
- Database migration as an ECS one-off task using the exact release image.
- ECS deployment waits for stable service.

## Remaining external setup

These cannot be completed purely inside the repository:

1. Create/validate the ACM certificate for the real production domain.
2. Create the Route 53 record pointing the domain to the ALB.
3. Populate the Secrets Manager application secret with the production `SECRET_KEY`.
4. Configure the GitHub `AWS_ROLE_ARN` secret from Terraform output.
5. Run `terraform plan` and review cost/security changes before `apply`.

Do not expose production HTTP directly; keep `enable_https=true`.
