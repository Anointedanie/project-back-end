# CI/CD Setup Guide for Backend Deployment

This guide explains how to set up Continuous Integration and Continuous Deployment (CI/CD) for the Django backend application using GitHub Actions and AWS EKS.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [GitHub Actions Workflow](#github-actions-workflow)
- [Secrets Configuration](#secrets-configuration)
- [Deployment Strategies](#deployment-strategies)
- [Rollback Procedures](#rollback-procedures)
- [Monitoring and Alerts](#monitoring-and-alerts)

## 🎯 Overview

The CI/CD pipeline automates the following:

1. **Build** - Run tests and build Docker image
2. **Push** - Push image to Amazon ECR
3. **Deploy** - Update Kubernetes deployment with new image
4. **Verify** - Check deployment health and rollback if needed

### Pipeline Triggers

- **Push to `main`** - Deploy to production
- **Pull Request** - Run tests only (no deployment)
- **Manual** - Trigger deployment manually via workflow_dispatch

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub                                   │
│                                                                   │
│  Developer Push ──▶ GitHub Actions Workflow                     │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Checkout Code                                         │  │
│  │  2. Run Tests (pytest)                                    │  │
│  │  3. Build Docker Image                                    │  │
│  │  4. Tag with commit SHA                                   │  │
│  └──────────────────────┬───────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Amazon ECR                                  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Push Image:                                              │  │
│  │  ecommerce/backend:${GITHUB_SHA}                         │  │
│  │  ecommerce/backend:latest                                │  │
│  └──────────────────────┬───────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS EKS                                     │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Update Deployment:                                       │  │
│  │  kubectl set image deployment/ecommerce-backend          │  │
│  │    ecommerce-backend=<new-image>                         │  │
│  │                                                            │  │
│  │  Rolling Update:                                           │  │
│  │  - Create new pod with new image                          │  │
│  │  - Wait for ready                                          │  │
│  │  - Terminate old pod                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 📦 Prerequisites

### 1. AWS IAM User for GitHub Actions

Create a dedicated IAM user with minimal permissions:

```bash
# Create IAM user
aws iam create-user --user-name github-actions-backend

# Create policy file
cat > github-actions-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster"
      ],
      "Resource": "arn:aws:eks:us-east-1:793796654438:cluster/ecommerce-eks"
    }
  ]
}
EOF

# Create policy
aws iam create-policy \
  --policy-name GitHubActionsBackendPolicy \
  --policy-document file://github-actions-policy.json

# Attach policy to user
aws iam attach-user-policy \
  --user-name github-actions-backend \
  --policy-arn arn:aws:iam::793796654438:policy/GitHubActionsBackendPolicy

# Create access keys
aws iam create-access-key --user-name github-actions-backend
```

Save the `AccessKeyId` and `SecretAccessKey` for later.

### 2. Kubernetes ServiceAccount for Deployment

Create a service account with permissions to update deployments:

```bash
# Create service account
kubectl create serviceaccount github-actions-deployer -n ecommerce

# Create role with deployment permissions
cat <<EOF | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployment-manager
  namespace: ecommerce
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "patch", "update"]
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
EOF

# Bind role to service account
kubectl create rolebinding github-actions-deployer-binding \
  --role=deployment-manager \
  --serviceaccount=ecommerce:github-actions-deployer \
  -n ecommerce

# Get service account token (Kubernetes 1.24+)
kubectl create token github-actions-deployer -n ecommerce --duration=8760h
```

Save the token for later.

## 🔐 Secrets Configuration

### GitHub Repository Secrets

Go to GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ACCESS_KEY_ID` | `AKIA...` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | `...` | IAM user secret key |
| `AWS_REGION` | `us-east-1` | AWS region |
| `AWS_ACCOUNT_ID` | `793796654438` | AWS account ID |
| `EKS_CLUSTER_NAME` | `ecommerce-eks` | EKS cluster name |
| `KUBE_CONFIG_DATA` | `<base64-encoded>` | Kubeconfig file (see below) |
| `ECR_REPOSITORY` | `ecommerce/backend` | ECR repository name |
| `SECRET_KEY` | `<django-secret-key>` | Django SECRET_KEY (50+ chars) |

**Note**: The `SECRET_KEY` is used to create the Kubernetes secret during deployment. The `deployment/secret.yaml` file is not pushed to GitHub for security.

### Generate KUBE_CONFIG_DATA

```bash
# Update kubeconfig
aws eks update-kubeconfig --name ecommerce-eks --region us-east-1

# Extract and base64 encode
cat ~/.kube/config | base64 -w 0

# Or use this one-liner
aws eks update-kubeconfig --name ecommerce-eks --region us-east-1 --dry-run | base64 -w 0
```

Paste the base64-encoded string as the `KUBE_CONFIG_DATA` secret.

## 🚀 GitHub Actions Workflow

Create `.github/workflows/deploy-backend.yml`:

```yaml
name: Deploy Backend to EKS

on:
  push:
    branches:
      - main
    paths:
      - 'backend/**'
      - '.github/workflows/deploy-backend.yml'
  pull_request:
    branches:
      - main
    paths:
      - 'backend/**'
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'production'
        type: choice
        options:
          - production
          - staging

env:
  AWS_REGION: ${{ secrets.AWS_REGION }}
  ECR_REPOSITORY: ${{ secrets.ECR_REPOSITORY }}
  EKS_CLUSTER_NAME: ${{ secrets.EKS_CLUSTER_NAME }}
  DEPLOYMENT_NAME: ecommerce-backend
  NAMESPACE: ecommerce

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        working-directory: ./backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run linting
        working-directory: ./backend
        run: |
          pip install flake8
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Run tests
        working-directory: ./backend
        run: |
          pip install pytest pytest-django
          pytest --maxfail=5 --disable-warnings
        env:
          DJANGO_SETTINGS_MODULE: config.settings
          SECRET_KEY: test-secret-key-for-ci
          DEBUG: True

  build-and-push:
    name: Build and Push to ECR
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Extract metadata
        id: meta
        run: |
          IMAGE_TAG=${GITHUB_SHA::7}
          echo "IMAGE_TAG=${IMAGE_TAG}" >> $GITHUB_OUTPUT
          echo "tags=${IMAGE_TAG}" >> $GITHUB_OUTPUT

      - name: Build Docker image
        working-directory: ./backend
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ steps.meta.outputs.IMAGE_TAG }}
        run: |
          docker build \
            --tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
            --tag $ECR_REGISTRY/$ECR_REPOSITORY:latest \
            --file Dockerfile \
            .

      - name: Push image to ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ steps.meta.outputs.IMAGE_TAG }}
        run: |
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

      - name: Image scan
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ steps.meta.outputs.IMAGE_TAG }}
        run: |
          aws ecr start-image-scan \
            --repository-name $ECR_REPOSITORY \
            --image-id imageTag=$IMAGE_TAG \
            --region $AWS_REGION || true

  deploy:
    name: Deploy to EKS
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Update kubeconfig
        run: |
          aws eks update-kubeconfig \
            --name $EKS_CLUSTER_NAME \
            --region $AWS_REGION

      - name: Deploy to EKS
        env:
          ECR_REGISTRY: ${{ secrets.AWS_ACCOUNT_ID }}.dkr.ecr.${{ secrets.AWS_REGION }}.amazonaws.com
          IMAGE_TAG: ${{ needs.build-and-push.outputs.image-tag }}
        run: |
          # Update deployment with new image
          kubectl set image deployment/$DEPLOYMENT_NAME \
            $DEPLOYMENT_NAME=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
            -n $NAMESPACE

          # Wait for rollout to complete
          kubectl rollout status deployment/$DEPLOYMENT_NAME \
            -n $NAMESPACE \
            --timeout=5m

      - name: Verify deployment
        run: |
          # Get pod status
          kubectl get pods -n $NAMESPACE -l app=ecommerce-backend

          # Check if pods are ready
          READY_PODS=$(kubectl get pods -n $NAMESPACE -l app=ecommerce-backend -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' | grep -o "True" | wc -l)

          if [ "$READY_PODS" -eq 0 ]; then
            echo "No pods are ready!"
            exit 1
          fi

          echo "Deployment successful: $READY_PODS pod(s) ready"

      - name: Rollback on failure
        if: failure()
        run: |
          echo "Deployment failed, rolling back..."
          kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE
          kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE

  notify:
    name: Send Notification
    runs-on: ubuntu-latest
    needs: [deploy]
    if: always()

    steps:
      - name: Send Slack notification
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: |
            Deployment Status: ${{ job.status }}
            Commit: ${{ github.sha }}
            Author: ${{ github.actor }}
          webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## 📋 Deployment Strategies

### 1. Rolling Update (Default)

Gradually replaces old pods with new ones:

```yaml
# In deployment.yaml
spec:
  replicas: 2
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Allow 1 extra pod during update
      maxUnavailable: 0  # No pods can be unavailable
```

**Pros**:
- Zero downtime
- Gradual rollout
- Easy to rollback

**Cons**:
- Slower deployment
- Mixed versions during rollout

### 2. Blue-Green Deployment

Deploy new version alongside old, then switch traffic:

```bash
# Deploy new version with different label
kubectl apply -f deployment-green.yaml

# Wait for ready
kubectl rollout status deployment/ecommerce-backend-green -n ecommerce

# Update service to point to new version
kubectl patch service ecommerce-backend-svc -n ecommerce \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Verify traffic
# If successful, delete old deployment
kubectl delete deployment ecommerce-backend-blue -n ecommerce
```

**Pros**:
- Instant traffic switch
- Easy rollback
- Testing in production environment

**Cons**:
- Requires double resources
- More complex setup

### 3. Canary Deployment

Gradually route traffic to new version:

```bash
# Deploy canary with 1 replica
kubectl apply -f deployment-canary.yaml

# Monitor metrics
# If stable, scale up canary and scale down stable
kubectl scale deployment ecommerce-backend-canary --replicas=2 -n ecommerce
kubectl scale deployment ecommerce-backend-stable --replicas=1 -n ecommerce

# Eventually replace all with canary
```

**Pros**:
- Reduced risk
- Real traffic testing
- Gradual rollout

**Cons**:
- Complex traffic management
- Longer deployment time
- Requires monitoring

## 🔄 Rollback Procedures

### Automatic Rollback

GitHub Actions workflow includes automatic rollback on failure:

```yaml
- name: Rollback on failure
  if: failure()
  run: |
    kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE
```

### Manual Rollback

```bash
# View rollout history
kubectl rollout history deployment/ecommerce-backend -n ecommerce

# Rollback to previous version
kubectl rollout undo deployment/ecommerce-backend -n ecommerce

# Rollback to specific revision
kubectl rollout undo deployment/ecommerce-backend -n ecommerce --to-revision=3

# Check status
kubectl rollout status deployment/ecommerce-backend -n ecommerce
```

### Emergency Rollback

If automated rollback fails:

```bash
# 1. Identify last working image
aws ecr describe-images \
  --repository-name ecommerce/backend \
  --region us-east-1 \
  --query 'sort_by(imageDetails,& imagePushedAt)[-5:]' \
  --output table

# 2. Manually set image
kubectl set image deployment/ecommerce-backend \
  ecommerce-backend=793796654438.dkr.ecr.us-east-1.amazonaws.com/ecommerce/backend:<working-tag> \
  -n ecommerce

# 3. Scale to safe state if needed
kubectl scale deployment/ecommerce-backend --replicas=1 -n ecommerce

# 4. Monitor
kubectl get pods -n ecommerce -w
```

## 📊 Monitoring and Alerts

### CloudWatch Logs

```bash
# Enable container insights
aws eks update-cluster-config \
  --name ecommerce-eks \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}'

# View logs
aws logs tail /aws/eks/ecommerce-eks/cluster --follow
```

### Kubernetes Metrics

```bash
# Install metrics server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# View resource usage
kubectl top nodes
kubectl top pods -n ecommerce
```

### Health Checks

Add to deployment:

```yaml
livenessProbe:
  httpGet:
    path: /health/
    port: 8000
  initialDelaySeconds: 60
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health/
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 5
```

Create Django health endpoint:

```python
# accounts/views.py or create health app
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Health check endpoint for Kubernetes"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return JsonResponse({
            'status': 'healthy',
            'database': 'connected'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
```

### Slack Notifications

Add Slack webhook to GitHub secrets:

1. Create Slack app: https://api.slack.com/apps
2. Enable Incoming Webhooks
3. Create webhook URL
4. Add to GitHub secrets as `SLACK_WEBHOOK_URL`

The workflow will send notifications on deployment success/failure.

## 🔍 Troubleshooting CI/CD

### Pipeline Failures

**Tests failing**:
```bash
# Run tests locally first
cd backend
python manage.py test

# Check test coverage
pytest --cov=. --cov-report=html
```

**Image push failing**:
- Check ECR permissions
- Verify AWS credentials
- Check repository exists

**Deployment failing**:
```bash
# Check deployment status
kubectl describe deployment ecommerce-backend -n ecommerce

# View events
kubectl get events -n ecommerce --sort-by='.lastTimestamp'

# Check pod logs
kubectl logs -l app=ecommerce-backend -n ecommerce --tail=100
```

### Common Issues

1. **Image pull errors** - Verify ECR permissions in pod's service account
2. **Deployment timeout** - Increase `--timeout` or check readiness probes
3. **Rollback not working** - Check revision history exists
4. **Secrets not updated** - Update ConfigMap/Secret after deployment

## 📚 Best Practices

1. **Always run tests** before deployment
2. **Tag images** with commit SHA for traceability
3. **Use Rolling Updates** for zero-downtime deployments
4. **Monitor metrics** during and after deployment
5. **Keep rollback ready** - test rollback procedures regularly
6. **Use separate environments** (staging/production)
7. **Implement health checks** for automatic recovery
8. **Set resource limits** to prevent resource exhaustion
9. **Use secrets management** - never commit secrets
10. **Document changes** in commit messages

## 🎯 Next Steps

1. Set up staging environment
2. Implement automated testing
3. Add performance monitoring
4. Configure alerting rules
5. Set up log aggregation
6. Implement security scanning
7. Add database migration automation
8. Configure backup procedures

## 📄 References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Kubernetes Deployment Strategies](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
