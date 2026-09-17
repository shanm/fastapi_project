# AWS deployment

This is the Phase 7 production infrastructure for the FastAPI service.

## AWS resources

- VPC with public, private application and private data subnets
- NAT Gateway
- ALB
- HTTPS/ACM support
- ECS Fargate
- ECR with immutable tags and lifecycle cleanup
- RDS PostgreSQL Multi-AZ, encrypted and backed up
- ElastiCache Redis with TLS, encryption and failover
- Secrets Manager
- CloudWatch logs and alarms
- ECS CPU autoscaling
- GitHub Actions OIDC role

## Required variables

Copy:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Set:

- `db_username`
- `github_repository`
- `acm_certificate_arn`

`enable_https` is true by default.

## Deployment

```bash
terraform init
terraform fmt -recursive
terraform validate
terraform plan
terraform apply
```

After apply:

1. Put a strong `SECRET_KEY` into the application Secrets Manager secret.
2. Configure GitHub repository secret `AWS_ROLE_ARN` using the Terraform output.
3. Ensure the ACM certificate covers the production DNS name.
4. Point Route 53 DNS at the ALB.
5. Push to `main`.

## CI/CD behavior

```text
GitHub
  ↓
Tests + migrations against CI services
  ↓
Docker build
  ↓
ECR immutable SHA image
  ↓
Register ECS task definition
  ↓
Run Alembic as one-off ECS task
  ↓
If migration succeeds
  ↓
Update ECS service
  ↓
Wait for stable deployment
```

ECS deployment circuit-breaker rollback is enabled.

## Important

Do not commit `terraform.tfvars`, `.env`, credentials, or secret values.

The first production deployment should be reviewed with:

```bash
terraform plan
```

because NAT Gateway, Multi-AZ RDS, Redis, ALB, ECS and CloudWatch incur AWS charges.
