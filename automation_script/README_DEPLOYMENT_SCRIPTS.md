# Backend Deployment Automation Scripts

Comprehensive automation scripts for deploying the E-commerce Django Backend to AWS EKS (Elastic Kubernetes Service).

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Scripts Description](#scripts-description)
- [Quick Start](#quick-start)
- [Detailed Usage](#detailed-usage)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)

## 🎯 Overview

These Python scripts automate the complete deployment lifecycle for the Django backend application on AWS EKS:

1. **Prerequisites checking** - Verify all required tools and configurations
2. **IRSA setup** - Configure IAM Roles for Service Accounts
3. **Application deployment** - Deploy all Kubernetes resources
4. **Resource cleanup** - Safely remove all deployed resources

## 📦 Prerequisites

### Required Tools

- **Python 3.7+** - For running automation scripts
- **kubectl** - Kubernetes CLI tool ([Install](https://kubernetes.io/docs/tasks/tools/))
- **AWS CLI v2** - AWS Command Line Interface ([Install](https://aws.amazon.com/cli/))
- **Docker** - For building container images ([Install](https://docs.docker.com/get-docker/))

### Required AWS Resources

- **EKS Cluster** - `ecommerce-eks` (already created)
- **RDS PostgreSQL Database** - Database instance with credentials
- **AWS Secrets Manager** - Secret named `ecommerce2` with database credentials
- **ECR Repository** - `ecommerce/backend` for container images
- **KMS Key** - For encrypting secrets (optional but recommended)

### AWS Permissions

Your AWS user/role needs permissions for:
- EKS cluster access
- IAM (create/update roles and policies)
- Secrets Manager (read secrets)
- ECR (push/pull images)
- KMS (decrypt secrets)

## 📝 Scripts Description

### 1. `check_prerequisites.py`

**Purpose**: Validate that all required tools, configurations, and AWS resources are ready.

**What it checks**:
- ✓ CLI tools (kubectl, AWS CLI, Docker)
- ✓ AWS credentials configuration
- ✓ Kubernetes cluster connectivity
- ✓ Namespace existence
- ✓ Service account and IRSA setup
- ✓ AWS Secrets Manager secret
- ✓ IAM role and policy
- ✓ ECR repository and images
- ✓ Nginx ingress controller

**Usage**:
```bash
cd automation_script/
./check_prerequisites.py
```

**Output**:
- Green ✓ - Check passed
- Red ✗ - Check failed (must fix)
- Yellow ⚠ - Warning (recommended to fix)

### 2. `setup_irsa.py`

**Purpose**: Configure IRSA (IAM Roles for Service Accounts) to allow pods to access AWS Secrets Manager securely without hardcoded credentials.

**What it does**:
1. Gets EKS cluster's OIDC provider
2. Creates IAM policy with Secrets Manager and KMS permissions
3. Creates IAM role with trust relationship to the OIDC provider
4. Attaches policy to role
5. Creates Kubernetes service account with IAM role annotation

**Configuration** (in script):
```python
config = {
    'cluster_name': 'ecommerce-eks',
    'region': 'us-east-1',
    'account_id': '793796654438',
    'namespace': 'ecommerce-backend-ns',
    'service_account_name': 'backend-auth-sa',
    'policy_name': 'BackendAuthSecretsManagerPolicy',
    'role_name': 'EKSBackendAuthRole',
    'secret_name': 'ecommerce2',
}
```

**Usage**:
```bash
cd automation_script/
chmod +x setup_irsa.py
./setup_irsa.py
```

**Expected Output**:
```
====================================================================
  IRSA SETUP FOR EKS BACKEND
====================================================================

Configuration:
  Cluster:         ecommerce-eks
  Region:          us-east-1
  Account ID:      793796654438
  Namespace:       ecommerce-backend-ns
  Service Account: backend-auth-sa
  ...

Continue? (y/N): y

============================================================
Getting OIDC Provider
============================================================
✓ OIDC Provider ARN: arn:aws:iam::...

✓ IRSA SETUP COMPLETE!
```

**Important Notes**:
- Run this ONCE before first deployment
- Script is idempotent (safe to run multiple times)
- If you get KMS access denied later, you may need to update the KMS key policy manually

### 3. `deploy_backend.py`

**Purpose**: Deploy the complete backend application to Kubernetes.

**What it deploys**:
1. ConfigMap (non-sensitive configuration)
2. Secret (sensitive data like Django SECRET_KEY)
3. Deployment (backend pods)
4. Service (internal load balancer)
5. Ingress (external access via nginx)

**Configuration**:
```python
NAMESPACE = "ecommerce-backend-ns"
DEPLOYMENT_NAME = "ecommerce-backend"
SERVICE_NAME = "ecommerce-backend-svc"
INGRESS_NAME = "ecommerce-backend-ingress"
```

**YAML Files** (relative paths):
```
../deployment/configmap.yaml
../deployment/secret.yaml
../deployment/deployment.yaml
../deployment/service.yaml
../deployment/backend_ingress.yaml
```

**Usage**:
```bash
cd automation_script/
chmod +x deploy_backend.py
./deploy_backend.py
```

**Expected Output**:
```
======================================================================
  E-COMMERCE BACKEND DEPLOYMENT AUTOMATION
======================================================================

✓ kubectl found (version: v1.28.0)
✓ Connected to Kubernetes cluster

[STEP 1] Checking namespace 'ecommerce'...
✓ Namespace 'ecommerce' exists

[STEP 2] Applying ConfigMap...
✓ Applied ../deployment/configmap.yaml

...

======================================================================
  DEPLOYMENT COMPLETED! 🎉
======================================================================
```

**Deployment Flow**:
1. Validates cluster connection
2. Checks namespace exists
3. Applies ConfigMap and Secret
4. Deploys application
5. Creates Service and Ingress
6. Waits for pods to be ready
7. Displays access URLs

**Post-Deployment**:
```bash
# Check pod status
kubectl get pods -n ecommerce

# View logs
kubectl logs -f deployment/ecommerce-backend -n ecommerce

# Test API
curl http://authen.ndiliatalents.com/api/auth/login
```

### 4. `destroy_backend.py`

**Purpose**: Safely remove all backend resources from the cluster.

**What it deletes**:
- ✓ Ingress
- ✓ Service
- ✓ Deployment (and pods)
- ✓ ConfigMap
- ✓ Secret

**What it preserves**:
- ℹ Namespace (may be used by other services)
- ℹ ServiceAccount (used by IRSA)
- ℹ IAM Role and Policy (can be reused)

**Usage**:
```bash
cd automation_script/
chmod +x destroy_backend.py
./destroy_backend.py
```

**Safety Features**:
- Requires explicit confirmation (`yes`)
- Shows what will be deleted
- Waits for pods to terminate cleanly
- Preserves IAM resources for reuse

**Example Session**:
```
WARNING: This will delete all backend resources!
Namespace: backend-ecommerce-ns

Resources to be deleted:
  - Ingress
  - Service
  - Deployment
  - ConfigMap
  - Secret

Are you sure you want to continue? (yes/NO): yes

[STEP 1] Deleting Ingress...
✓ Deleted ingress/ecommerce-backend-ingress

...

DESTRUCTION COMPLETED! ✓
```

## 🚀 Quick Start

### First Time Setup (Local Development)

```bash
# 1. Navigate to deployment directory
cd /home/chris/Desktop/shopify_project/backend_python_auth/backend/deployment/

# 2. Create secret.yaml from template
cp secret.yaml.template secret.yaml

# 3. Generate Django SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 4. Edit secret.yaml and paste the generated key
nano secret.yaml  # or use your preferred editor

# 5. Navigate to automation scripts
cd ../automation_script/

# 6. Make scripts executable
chmod +x *.py

# 7. Check prerequisites
./check_prerequisites.py

# 8. Setup IRSA (one-time)
./setup_irsa.py

# 9. Deploy application
./deploy_backend.py
```

**Note**: The `secret.yaml` file is gitignored and won't be committed to version control.

### Subsequent Deployments

```bash
# Build new image
cd /home/chris/Desktop/shopify_project/backend_python_auth/backend/
docker build -t 793796654438.dkr.ecr.us-east-1.amazonaws.com/ecommerce/backend:v1.1 .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 793796654438.dkr.ecr.us-east-1.amazonaws.com
docker push 793796654438.dkr.ecr.us-east-1.amazonaws.com/ecommerce/backend:v1.1

# Update deployment YAML with new tag
# Then redeploy
cd automation_script/
./deploy_backend.py
```

### Clean Up

```bash
# Remove all resources
cd automation_script/
./destroy_backend.py

# Optionally delete namespace
kubectl delete namespace ecommerce
```

## 🔍 Detailed Usage

### Environment Configuration

The scripts use these default values:

| Variable | Value | Description |
|----------|-------|-------------|
| `CLUSTER_NAME` | `ecommerce-eks` | EKS cluster name |
| `REGION` | `us-east-1` | AWS region |
| `ACCOUNT_ID` | `793796654438` | AWS account ID |
| `NAMESPACE` | `ecommerce` | Kubernetes namespace |
| `SECRET_NAME` | `ecommerce2` | Secrets Manager secret name |

To modify, edit the configuration section in each script.

### ConfigMap vs Secret

**ConfigMap** (`deployment/configmap.yaml`):
- Non-sensitive configuration
- Environment variables for Django
- AWS region and secret name
- Debug and allowed hosts settings

**Secret** (`deployment/secret.yaml`):
- Sensitive data (base64 encoded)
- Django SECRET_KEY
- Can add API keys, tokens, etc.
- **Note**: `secret.yaml` is gitignored for security
- For local development: Copy `secret.yaml.template` to `secret.yaml` and fill in values
- For CI/CD: Secret is created automatically from GitHub Actions secrets

### IRSA (IAM Roles for Service Accounts)

IRSA allows Kubernetes pods to assume IAM roles without hardcoding AWS credentials.

**How it works**:
1. EKS cluster has an OIDC provider
2. IAM role trusts this OIDC provider
3. Service account is annotated with IAM role ARN
4. Pods using this service account can assume the role
5. AWS SDK automatically uses the role credentials

**Permissions granted**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:793796654438:secret:ecommerce2-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey"
      ],
      "Resource": "*"
    }
  ]
}
```

### Ingress Configuration

The backend uses nginx ingress controller:

**Domain**: `authen.ndiliatalents.com`
**Protocol**: HTTP (TLS section commented out)
**Path**: `/` (all requests)
**Backend**: `ecommerce-backend-svc:80`

**Annotations**:
- `nginx.ingress.kubernetes.io/ssl-redirect: "false"` - Disable HTTPS redirect

## 🐛 Troubleshooting

### Common Issues

#### 1. Pods Not Starting

**Symptom**: Pods in `CrashLoopBackOff` or `Error` state

**Check**:
```bash
kubectl get pods -n ecommerce
kubectl logs <pod-name> -n ecommerce
kubectl describe pod <pod-name> -n ecommerce
```

**Common Causes**:
- Database connection failure (check RDS security group)
- Secrets Manager access denied (verify IRSA setup)
- KMS decrypt permission missing (update KMS key policy)
- Image pull error (verify ECR permissions)

#### 2. KMS Access Denied

**Error**: `An error occurred (AccessDeniedException) when calling the GetSecretValue operation`

**Solution**:
Update KMS key policy to include the IAM role:

```bash
# Get KMS key ID
aws secretsmanager describe-secret --secret-id ecommerce2 --region us-east-1 --query 'KmsKeyId' --output text

# Update key policy (via AWS Console or CLI)
# Add to the key policy:
{
  "Sid": "Allow EKS Backend Role",
  "Effect": "Allow",
  "Principal": {
    "AWS": "arn:aws:iam::793796654438:role/EKSBackendAuthRole"
  },
  "Action": [
    "kms:Decrypt",
    "kms:DescribeKey"
  ],
  "Resource": "*"
}
```

#### 3. Database Connection Timeout

**Error**: `could not connect to server: Connection timed out`

**Solution**:
Update RDS security group to allow traffic from EKS worker nodes:

```bash
# Get EKS worker node security group
aws eks describe-cluster --name ecommerce-eks --region us-east-1 --query 'cluster.resourcesVpcConfig.securityGroupIds'

# Add inbound rule to RDS security group:
# Type: PostgreSQL
# Protocol: TCP
# Port: 5432
# Source: <eks-worker-security-group>
```

#### 4. Ingress Not Working

**Symptom**: Can't access application via domain

**Check**:
```bash
kubectl get ingress -n ecommerce
kubectl describe ingress ecommerce-backend-ingress -n ecommerce
```

**Common Causes**:
- Nginx ingress controller not installed
- DNS not pointing to load balancer
- Multiple ingress resources causing conflicts

**Solution**:
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Get load balancer address
kubectl get svc -n ingress-nginx

# Update DNS A record to point to load balancer
```

#### 5. Pod Can't Access Secrets Manager

**Check IRSA setup**:
```bash
# Verify service account has role annotation
kubectl describe sa backend-auth-sa -n ecommerce

# Check if pod is using the service account
kubectl get pod <pod-name> -n ecommerce -o yaml | grep serviceAccount

# Test from within pod
kubectl exec -it <pod-name> -n ecommerce -- aws sts get-caller-identity
```

### Debug Commands

```bash
# View all resources in namespace
kubectl get all -n ecommerce

# Check events
kubectl get events -n ecommerce --sort-by='.lastTimestamp'

# View pod logs
kubectl logs -f deployment/ecommerce-backend -n ecommerce

# Exec into pod
kubectl exec -it <pod-name> -n ecommerce -- /bin/bash

# Test secrets access from pod
kubectl exec -it <pod-name> -n ecommerce -- aws secretsmanager get-secret-value --secret-id ecommerce2 --region us-east-1

# Check environment variables in pod
kubectl exec -it <pod-name> -n ecommerce -- env | grep -E 'AWS|DB'

# Restart deployment
kubectl rollout restart deployment/ecommerce-backend -n ecommerce

# View deployment history
kubectl rollout history deployment/ecommerce-backend -n ecommerce
```

## 🏗️ Architecture

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Route 53 / DNS                            │
│              authen.ndiliatalents.com                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               AWS Network Load Balancer                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│           Nginx Ingress Controller (EKS)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               Kubernetes Ingress                             │
│           ecommerce-backend-ingress                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            Kubernetes Service (ClusterIP)                    │
│             ecommerce-backend-svc:80                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend Pods                                │
│         ┌──────────────┐  ┌──────────────┐                 │
│         │   Pod 1      │  │   Pod 2      │                 │
│         │ Django:8000  │  │ Django:8000  │                 │
│         └──────────────┘  └──────────────┘                 │
│                                                              │
│  Environment from: ConfigMap + Secret                        │
│  Service Account: backend-auth-sa (IRSA)                     │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌─────────────────┐ ┌──────────────┐ ┌──────────────┐
│  AWS Secrets    │ │  RDS         │ │  KMS         │
│  Manager        │ │  PostgreSQL  │ │  (Encryption)│
│  (ecommerce2)   │ │              │ │              │
└─────────────────┘ └──────────────┘ └──────────────┘
```

### IRSA (IAM Roles for Service Accounts) Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      EKS Cluster                             │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Pod: ecommerce-backend                 │    │
│  │                                                      │    │
│  │  1. AWS SDK needs credentials                       │    │
│  │  2. Checks environment (no hardcoded creds)         │    │
│  │  3. Finds service account token                     │    │
│  │  4. Uses token to assume IAM role                   │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                      │
│  ┌────────────────────▼───────────────────────────────┐    │
│  │       ServiceAccount: backend-auth-sa                │    │
│  │                                                      │    │
│  │  Annotation:                                         │    │
│  │  eks.amazonaws.com/role-arn:                        │    │
│  │    arn:aws:iam::...:role/EKSBackendAuthRole         │    │
│  └────────────────────┬───────────────────────────────┘    │
│                       │                                      │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        ▼ (AssumeRoleWithWebIdentity)
┌─────────────────────────────────────────────────────────────┐
│                     AWS IAM                                  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         IAM Role: EKSBackendAuthRole                │    │
│  │                                                      │    │
│  │  Trust Policy:                                       │    │
│  │  - Principal: OIDC Provider (EKS cluster)           │    │
│  │  - Condition: serviceaccount matches                │    │
│  │                                                      │    │
│  │  Attached Policy:                                    │    │
│  │  - BackendAuthSecretsManagerPolicy                  │    │
│  └────────────────────┬───────────────────────────────┘    │
└────────────────────────┼──────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│  Secrets Manager │            │       KMS        │
│                  │            │                  │
│  Permissions:    │            │  Permissions:    │
│  - GetSecret     │            │  - Decrypt       │
│  - DescribeSecret│            │  - DescribeKey   │
└──────────────────┘            └──────────────────┘
```

## 📚 Additional Resources

- [EKS IRSA Documentation](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Nginx Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)

## 📄 License

Part of the E-commerce Backend project.
