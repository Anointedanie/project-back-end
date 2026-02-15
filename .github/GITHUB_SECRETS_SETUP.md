# GitHub Actions Secrets Setup

## Required Secrets for Backend CI/CD

Go to: **Repository → Settings → Secrets and variables → Actions → New repository secret**

Add the following secrets:

| Secret Name | Example Value | Description |
|-------------|---------------|-------------|
| `AWS_ACCESS_KEY_ID` | `AKIA...` | IAM user access key with ECR, EKS, and Secrets Manager permissions |
| `AWS_SECRET_ACCESS_KEY` | `***` | IAM user secret access key |
| `AWS_REGION` | `us-east-1` | AWS region where EKS cluster is deployed |
| `EKS_CLUSTER_NAME` | `ecommerce-eks` | Name of your EKS cluster |
| `IMAGE_NAME` | `ecommerce/backend` | ECR repository name (same as ECR_REPOSITORY) |
| `ECR_REPOSITORY` | `ecommerce/backend` | ECR repository name for the backend image |
| `SECRET_KEY` | `<50+ char random string>` | Django SECRET_KEY |

## How to Get Values

### 1. AWS Credentials
```bash
# These should be from the IAM user created for GitHub Actions
# See CI-CD_SETUP.md for creating the IAM user
aws iam create-access-key --user-name github-actions-backend.
```

### 2. AWS Region
```bash
# Your EKS cluster region
us-east-1
```

### 3. EKS Cluster Name
```bash
# Check your cluster name
aws eks list-clusters --region us-east-1
```

### 4. IMAGE_NAME / ECR_REPOSITORY
```bash
# Both should be set to: ecommerce/backend
# This is your ECR repository name (not the full URI)
ecommerce/backend
```

### 5. SECRET_KEY
```bash
# Generate a secure Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Verify Secrets Are Set

After adding all secrets, you should see:
- ✓ AWS_ACCESS_KEY_ID
- ✓ AWS_SECRET_ACCESS_KEY
- ✓ AWS_REGION
- ✓ EKS_CLUSTER_NAME
- ✓ IMAGE_NAME
- ✓ ECR_REPOSITORY
- ✓ SECRET_KEY

## What the Workflow Does

### Job 1: Build and Push
1. Checks out code
2. Configures AWS credentials
3. Logs into ECR
4. Builds Docker image
5. Pushes to ECR
6. Updates deployment.yaml with new image tag
7. Commits and pushes updated deployment.yaml

### Job 2: Deploy
1. Checks out code (with latest deployment.yaml)
2. Configures AWS credentials
3. **Sets up prerequisites** (installs kubectl, configures cluster access)
4. Sets up IRSA (if needed)
5. **Creates Kubernetes secret from GitHub secret**
6. Deploys to EKS

## Important Notes

### AWS Credentials Handling
The workflow now properly passes AWS credentials to sudo:
```yaml
sudo -E \
  AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
  AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
  AWS_DEFAULT_REGION="${AWS_REGION:-us-east-1}" \
  AWS_REGION="${AWS_REGION:-us-east-1}" \
  HOME="${HOME}" \
  ./check_prerequisites.py
```

### Kubernetes Secret Management
The `SECRET_KEY` secret is **not stored in Git**. Instead:
- For CI/CD: Created from GitHub Actions secret
- For Local: Created from `secret.yaml` file (gitignored)

### IMAGE_NAME vs ECR_REPOSITORY
Both should be set to `ecommerce/backend`:
- `IMAGE_NAME`: Used during Docker build/push
- `ECR_REPOSITORY`: Referenced in documentation/scripts
- They should have the **same value**

## Troubleshooting

### "AWS credentials not configured"
- Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set in GitHub secrets
- Check that secrets are not expired
- Ensure IAM user has necessary permissions

### "Cannot connect to Kubernetes cluster"
- Verify `EKS_CLUSTER_NAME` matches your actual cluster name
- Check that IAM user has EKS describe permissions
- Ensure cluster is in the correct region

### "ECR repository not found"
- Verify `IMAGE_NAME` and `ECR_REPOSITORY` are set to `ecommerce/backend`
- Check that the ECR repository exists:
  ```bash
  aws ecr describe-repositories --repository-names ecommerce/backend --region us-east-1
  ```

### "Secret not found in cluster"
- The workflow creates it automatically in the "Create/Update Kubernetes Secret" step
- If this step fails, check that `SECRET_KEY` is set in GitHub secrets
- Verify namespace exists before secret creation

## Security Best Practices

1. ✅ Use IAM user with minimal required permissions
2. ✅ Rotate access keys regularly
3. ✅ Never commit secrets to Git
4. ✅ Use different secrets for dev/staging/prod
5. ✅ Enable GitHub secret access logging
6. ✅ Limit who can access GitHub secrets

## Related Documentation

- `automation_script/CI-CD_SETUP.md` - Full CI/CD setup guide
- `automation_script/README_DEPLOYMENT_SCRIPTS.md` - Deployment scripts documentation
- `SECRETS_SETUP.md` - Secrets management guide
