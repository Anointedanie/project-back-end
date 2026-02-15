# Secrets Management Setup

## 🔒 Overview

The backend deployment now uses **GitHub Actions secrets** for managing sensitive data, eliminating the need to commit `secret.yaml` to version control.

## ✅ What Changed

### 1. **Gitignore Updated**
- `deployment/secret.yaml` is now gitignored
- File: `.gitignore`

### 2. **Template Created**
- Created `deployment/secret.yaml.template` as a reference
- Contains structure and instructions for local development

### 3. **CI/CD Workflow Updated**
- Added step to create Kubernetes secret from GitHub Actions secret
- File: `.github/workflows/ci-cd.yaml`
- New step: "Create/Update Kubernetes Secret"

```yaml
- name: Create/Update Kubernetes Secret
  run: |
    kubectl create secret generic backend-secrets \
      --from-literal=SECRET_KEY="${{ secrets.SECRET_KEY }}" \
      --namespace=${{ env.NAMESPACE }} \
      --dry-run=client -o yaml | kubectl apply -f -
```

### 4. **Deployment Script Updated**
- `deploy_backend.py` now checks if `secret.yaml` exists
- If missing, it verifies the secret exists in the cluster
- Skips applying secret.yaml if it doesn't exist (CI/CD mode)
- File: `automation_script/deploy_backend.py`

### 5. **Documentation Updated**
- `README_DEPLOYMENT_SCRIPTS.md` - Added local setup instructions
- `CI-CD_SETUP.md` - Added SECRET_KEY to GitHub secrets table

## 🚀 Usage

### For Local Development

```bash
# 1. Create secret.yaml from template
cd deployment/
cp secret.yaml.template secret.yaml

# 2. Generate a Django SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 3. Edit secret.yaml and add the generated key
nano secret.yaml

# 4. Deploy as usual
cd ../automation_script/
./deploy_backend.py
```

### For CI/CD (GitHub Actions)

1. **Add GitHub Secret**:
   - Go to: Repository → Settings → Secrets and variables → Actions
   - Add new secret: `SECRET_KEY`
   - Value: Your Django secret key (50+ characters)

2. **Workflow Behavior**:
   - On push to main, workflow automatically:
     - Builds and pushes Docker image
     - Sets up IRSA
     - **Creates Kubernetes secret from GitHub secret**
     - Deploys application

3. **No Manual Steps Required**:
   - Secret is created/updated automatically
   - No need to manage `secret.yaml` in Git

## 🔐 Security Benefits

1. ✅ **No Secrets in Git**: `secret.yaml` never committed to repository
2. ✅ **Centralized Management**: Secrets managed in GitHub Actions
3. ✅ **Audit Trail**: GitHub tracks who accessed/modified secrets
4. ✅ **Easy Rotation**: Update secret in GitHub, redeploy automatically
5. ✅ **Environment Isolation**: Different secrets for dev/staging/prod

## 📋 GitHub Actions Secrets Required

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | IAM user access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key | `***` |
| `AWS_REGION` | AWS region | `us-east-1` |
| `EKS_CLUSTER_NAME` | EKS cluster name | `ecommerce-eks` |
| `ECR_REPOSITORY` | ECR repository | `ecommerce/backend` |
| **`SECRET_KEY`** | **Django secret key** | **50+ random chars** |

## 🛠️ Troubleshooting

### Local Deployment Fails

**Error**: `Secret 'backend-secrets' not found in cluster!`

**Solution**:
```bash
# Option 1: Create secret.yaml from template
cp deployment/secret.yaml.template deployment/secret.yaml
# Edit and fill in values
nano deployment/secret.yaml

# Option 2: Create secret directly in cluster
kubectl create secret generic backend-secrets \
  --from-literal=SECRET_KEY="your-secret-key-here" \
  -n ecommerce-backend-ns
```

### CI/CD Deployment Fails

**Error**: Secret not being created

**Solution**:
1. Verify `SECRET_KEY` is added to GitHub Actions secrets
2. Check workflow logs for the "Create/Update Kubernetes Secret" step
3. Ensure namespace exists before secret creation

## 📚 Related Files

- `.gitignore` - Excludes secret.yaml
- `deployment/secret.yaml.template` - Template for local development
- `.github/workflows/ci-cd.yaml` - CI/CD workflow with secret creation
- `automation_script/deploy_backend.py` - Deployment script
- `automation_script/README_DEPLOYMENT_SCRIPTS.md` - Full documentation
- `automation_script/CI-CD_SETUP.md` - CI/CD setup guide

## ✨ Best Practices

1. **Never commit secret.yaml** - It's gitignored, keep it that way
2. **Use strong secret keys** - 50+ characters, random
3. **Rotate secrets regularly** - Update GitHub secret, redeploy
4. **Different secrets per environment** - Dev, staging, prod
5. **Limit access** - Only necessary people have access to GitHub secrets

## 🎯 Next Steps

1. ✅ Remove existing `secret.yaml` from Git if it was committed
2. ✅ Add `SECRET_KEY` to GitHub Actions secrets
3. ✅ Test local deployment with template
4. ✅ Verify CI/CD pipeline works correctly
