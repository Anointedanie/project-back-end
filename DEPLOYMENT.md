# Django Backend Deployment Guide

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [How the Application Works with Docker](#how-the-application-works-with-docker)
- [AWS Secrets Manager Integration](#aws-secrets-manager-integration)
- [Local Development Setup](#local-development-setup)
- [AWS EKS Deployment](#aws-eks-deployment)
- [GitHub Actions CI/CD Pipeline](#github-actions-cicd-pipeline)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                           │
│  1. Build Docker Image                                       │
│  2. Push to Amazon ECR                                       │
│  3. Deploy to EKS                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Amazon ECR                               │
│  Container Registry for Docker Images                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Amazon EKS Cluster                       │
│  ┌───────────────────────────────────────────────┐          │
│  │  Pod: backend-auth                             │          │
│  │  - Django Application (Gunicorn)              │          │
│  │  - IAM Role for Service Account (IRSA)       │          │
│  │  - Kubernetes Secrets (non-sensitive config) │          │
│  └───────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS Secrets Manager                             │
│  - Database credentials (RDS)                                │
│  - API keys and sensitive secrets                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Amazon RDS (PostgreSQL)                  │
│  - Production Database                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## How the Application Works with Docker

### Multi-Stage Docker Build

The Dockerfile uses a **multi-stage build** pattern for optimization:

#### Stage 1: Builder
```dockerfile
FROM python:3.12-slim as builder
# Install build dependencies (gcc, postgresql-client, libpq-dev)
# Install Python packages to /install directory
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt
```

**Purpose:**
- Includes build tools (gcc) needed to compile Python packages
- Creates a temporary layer with all build dependencies
- Installs Python packages to a separate directory (`/install`)

#### Stage 2: Production
```dockerfile
FROM python:3.12-slim
# Copy only installed Python packages from builder
COPY --from=builder /install /usr/local
# Copy application code
COPY --chown=appuser:appuser . .
# Run as non-root user for security
USER appuser
```

**Purpose:**
- Creates a slim production image without build tools
- Reduces final image size (~500MB vs 1GB+)
- Enhances security by removing unnecessary packages
- Runs as non-root user (`appuser`)

### Application Startup Flow

```
entrypoint.sh → Environment Check → Database Connection → Gunicorn → Django App
```

1. **entrypoint.sh** - Initialization script that:
   - Waits for database (if `WAIT_FOR_DB=true`)
   - Runs migrations (if `RUN_MIGRATIONS=true`)
   - Collects static files (if `COLLECT_STATIC=true`)
   - Creates superuser (if `CREATE_SUPERUSER=true`)

2. **Gunicorn WSGI Server** - Production-ready server:
   - 4 worker processes
   - 2 threads per worker
   - 60-second timeout
   - Logs to stdout/stderr

---

## AWS Secrets Manager Integration

### How It Works

The application uses AWS Secrets Manager to securely retrieve sensitive credentials at runtime.

#### Configuration File: `config/utils/aws_secrets.py`

```python
def get_rds_credentials():
    """
    Retrieves RDS database credentials from AWS Secrets Manager.

    Flow:
    1. Uses boto3 SDK to connect to AWS Secrets Manager
    2. Retrieves secret by name (AWS_SECRET_NAME from env)
    3. Parses JSON secret value
    4. Returns database connection parameters
    """
    secret_name = config('AWS_SECRET_NAME')  # e.g., "ecommerce2"
    region_name = config('AWS_REGION')       # e.g., "us-east-1"

    # Create Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # Retrieve secret value
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])

    return {
        'NAME': secret['dbname'],
        'USER': secret['username'],
        'PASSWORD': secret['password'],
        'HOST': secret['host'],
        'PORT': secret['port']
    }
```

#### Settings Configuration: `config/settings.py`

```python
USE_AWS_SECRETS = config('USE_AWS_SECRETS', default='False')

if USE_AWS_SECRETS.strip().lower() in ['true', '1', 'yes', 'on']:
    # Production: Fetch from AWS Secrets Manager
    logger.info("Loading database credentials from AWS Secrets Manager")
    from config.utils.aws_secrets import get_rds_credentials
    db_config = get_rds_credentials()
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            **db_config
        }
    }
else:
    # Development: Use environment variables
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='postgres'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
```

### AWS IAM Authentication Flow

In Kubernetes/EKS, the application uses **IAM Roles for Service Accounts (IRSA)**:

```
Pod → Service Account → IAM Role → Secrets Manager → Retrieve Secret
```

**No AWS credentials needed in the container!** The IAM role is automatically assumed.

#### Required IAM Policy

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
      "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:ecommerce2-*"
    }
  ]
}
```

### Secret Format in AWS Secrets Manager

Store your RDS credentials in this JSON format:

```json
{
  "username": "dbuser",
  "password": "secure_password_here",
  "dbname": "postgres",
  "host": "your-rds-instance.region.rds.amazonaws.com",
  "port": "5432"
}
```

**To create/update the secret:**

```bash
aws secretsmanager create-secret \
  --name ecommerce2 \
  --description "RDS credentials for ecommerce backend" \
  --secret-string '{
    "username":"dbuser",
    "password":"secure_password",
    "dbname":"postgres",
    "host":"your-rds.us-east-1.rds.amazonaws.com",
    "port":"5432"
  }' \
  --region us-east-1
```

---

## Local Development Setup

### Option 1: Docker with AWS Credentials (Current Setup)

```bash
# Build the image
docker build -t backend-auth:latest .

# Run with AWS credentials mounted
docker run -d \
  --name backend-auth-container \
  --network host \
  --env-file .env \
  -v ~/.aws:/home/appuser/.aws:ro \
  backend-auth:latest
```

**Environment Variables (.env):**
```bash
USE_AWS_SECRETS=True
AWS_SECRET_NAME=ecommerce2
AWS_REGION=us-east-1
SECRET_KEY=your-django-secret-key
DEBUG=True
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
```

### Option 2: Local Database (No AWS)

```bash
# Update .env
USE_AWS_SECRETS=False
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=localpassword
DB_HOST=localhost
DB_PORT=5432

# Run container
docker run -d \
  --name backend-auth-container \
  -p 8000:8000 \
  --env-file .env \
  backend-auth:latest
```

### Option 3: Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: localpassword
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - USE_AWS_SECRETS=False
      - DB_NAME=postgres
      - DB_USER=postgres
      - DB_PASSWORD=localpassword
      - DB_HOST=db
      - DB_PORT=5432
      - SECRET_KEY=dev-secret-key-change-in-production
      - DEBUG=True
    depends_on:
      - db
    volumes:
      - ./staticfiles:/app/staticfiles
      - ./media:/app/media

volumes:
  postgres_data:
```

Run with:
```bash
docker-compose up -d
```

---

## AWS EKS Deployment

### Prerequisites

1. **AWS CLI** installed and configured
2. **kubectl** installed
3. **eksctl** installed (optional but recommended)
4. **EKS Cluster** already created
5. **ECR Repository** created
6. **RDS Database** running and accessible from EKS VPC
7. **AWS Secrets Manager** secret created with RDS credentials

### Step 1: Create IAM Role for Service Account (IRSA)

```bash
# Set variables
export CLUSTER_NAME=your-eks-cluster
export REGION=us-east-1
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export NAMESPACE=default
export SERVICE_ACCOUNT_NAME=backend-auth-sa

# Create IAM OIDC provider for your cluster (one-time setup)
eksctl utils associate-iam-oidc-provider \
  --cluster=$CLUSTER_NAME \
  --region=$REGION \
  --approve

# Create IAM policy for Secrets Manager access
cat > secrets-manager-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:$REGION:$ACCOUNT_ID:secret:ecommerce2-*"
    }
  ]
}
EOF

aws iam create-policy \
  --policy-name BackendAuthSecretsManagerPolicy \
  --policy-document file://secrets-manager-policy.json

# Create service account with IAM role
eksctl create iamserviceaccount \
  --name=$SERVICE_ACCOUNT_NAME \
  --namespace=$NAMESPACE \
  --cluster=$CLUSTER_NAME \
  --region=$REGION \
  --attach-policy-arn=arn:aws:iam::$ACCOUNT_ID:policy/BackendAuthSecretsManagerPolicy \
  --approve \
  --override-existing-serviceaccounts
```

### Step 2: Create Kubernetes Secrets (Non-sensitive Config)

```bash
# Create Kubernetes secret for non-sensitive environment variables
kubectl create secret generic backend-auth-config \
  --from-literal=SECRET_KEY='your-django-secret-key-generate-new-one' \
  --from-literal=JWT_ACCESS_TOKEN_LIFETIME='60' \
  --from-literal=JWT_REFRESH_TOKEN_LIFETIME='1440' \
  --namespace=default
```

**Important:** Store the Django `SECRET_KEY` as a Kubernetes secret, not in AWS Secrets Manager, as it's app-specific rather than infrastructure-specific.

### Step 3: Create Kubernetes Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-auth
  namespace: default
  labels:
    app: backend-auth
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend-auth
  template:
    metadata:
      labels:
        app: backend-auth
    spec:
      serviceAccountName: backend-auth-sa  # Links to IAM role via IRSA
      containers:
      - name: backend-auth
        image: ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/backend-auth:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          protocol: TCP
        env:
        # AWS Secrets Manager configuration
        - name: USE_AWS_SECRETS
          value: "True"
        - name: AWS_SECRET_NAME
          value: "ecommerce2"
        - name: AWS_REGION
          value: "us-east-1"

        # Application configuration from Kubernetes secrets
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: backend-auth-config
              key: SECRET_KEY

        - name: JWT_ACCESS_TOKEN_LIFETIME
          valueFrom:
            secretKeyRef:
              name: backend-auth-config
              key: JWT_ACCESS_TOKEN_LIFETIME

        - name: JWT_REFRESH_TOKEN_LIFETIME
          valueFrom:
            secretKeyRef:
              name: backend-auth-config
              key: JWT_REFRESH_TOKEN_LIFETIME

        # Other configuration
        - name: DEBUG
          value: "False"
        - name: ALLOWED_HOSTS
          value: "api.yourdomain.com,*.yourdomain.com"

        # Database migration settings
        - name: RUN_MIGRATIONS
          value: "true"
        - name: COLLECT_STATIC
          value: "true"

        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"

        livenessProbe:
          httpGet:
            path: /admin/
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /admin/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

---
apiVersion: v1
kind: Service
metadata:
  name: backend-auth-service
  namespace: default
spec:
  type: LoadBalancer  # or ClusterIP if using Ingress
  selector:
    app: backend-auth
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000

---
# Optional: Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-auth-hpa
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-auth
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Step 4: Optional - Create Ingress (ALB)

Create `k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: backend-auth-ingress
  namespace: default
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:ACCOUNT_ID:certificate/CERT_ID
    alb.ingress.kubernetes.io/ssl-redirect: '443'
spec:
  ingressClassName: alb
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend-auth-service
            port:
              number: 80
```

### Step 5: Deploy to EKS

```bash
# Update kubeconfig
aws eks update-kubeconfig --name $CLUSTER_NAME --region $REGION

# Apply Kubernetes manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/ingress.yaml  # if using ingress

# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/backend-auth

# Check if IAM role is attached
kubectl describe pod <pod-name> | grep AWS_ROLE_ARN
```

---

## GitHub Actions CI/CD Pipeline

### GitHub Secrets Configuration

Add these secrets to your GitHub repository:
**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `AWS_ACCOUNT_ID` | Your AWS Account ID | `123456789012` |
| `AWS_REGION` | AWS Region | `us-east-1` |
| `AWS_ACCESS_KEY_ID` | AWS Access Key for GitHub Actions | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `EKS_CLUSTER_NAME` | EKS Cluster Name | `production-cluster` |
| `ECR_REPOSITORY` | ECR Repository Name | `backend-auth` |
| `KUBE_CONFIG_DATA` | Base64 encoded kubeconfig (optional) | `<base64-encoded-config>` |

**To create AWS credentials for GitHub Actions:**

```bash
# Create IAM policy for GitHub Actions
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
      "Resource": "arn:aws:eks:us-east-1:ACCOUNT_ID:cluster/your-cluster"
    }
  ]
}
EOF

# Create IAM user for GitHub Actions
aws iam create-user --user-name github-actions-deployer
aws iam create-policy --policy-name GitHubActionsDeployPolicy --policy-document file://github-actions-policy.json
aws iam attach-user-policy --user-name github-actions-deployer --policy-arn arn:aws:iam::ACCOUNT_ID:policy/GitHubActionsDeployPolicy

# Create access keys
aws iam create-access-key --user-name github-actions-deployer
```

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Build and Deploy to EKS

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main

env:
  AWS_REGION: ${{ secrets.AWS_REGION }}
  ECR_REPOSITORY: ${{ secrets.ECR_REPOSITORY }}
  EKS_CLUSTER_NAME: ${{ secrets.EKS_CLUSTER_NAME }}

jobs:
  build-and-deploy:
    name: Build, Push to ECR, and Deploy to EKS
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ env.AWS_REGION }}

    - name: Login to Amazon ECR
      id: login-ecr
      uses: aws-actions/amazon-ecr-login@v1

    - name: Build, tag, and push image to Amazon ECR
      id: build-image
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        # Build Docker image
        docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
        docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest

        # Push to ECR
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
        docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

        # Output image URI for next steps
        echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT

    - name: Install kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'v1.28.0'

    - name: Update kube config
      run: |
        aws eks update-kubeconfig --name $EKS_CLUSTER_NAME --region $AWS_REGION

    - name: Deploy to EKS
      env:
        ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
        IMAGE_TAG: ${{ github.sha }}
      run: |
        # Update deployment with new image
        kubectl set image deployment/backend-auth \
          backend-auth=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG \
          --namespace=default

        # Wait for rollout to complete
        kubectl rollout status deployment/backend-auth --namespace=default --timeout=5m

        # Verify deployment
        kubectl get pods --namespace=default -l app=backend-auth

    - name: Verify deployment
      run: |
        kubectl get services backend-auth-service --namespace=default
        kubectl get ingress backend-auth-ingress --namespace=default

    - name: Run database migrations (Optional)
      run: |
        # Get first pod name
        POD_NAME=$(kubectl get pods --namespace=default -l app=backend-auth -o jsonpath="{.items[0].metadata.name}")

        # Run migrations
        kubectl exec $POD_NAME --namespace=default -- python manage.py migrate --noinput

        # Collect static files
        kubectl exec $POD_NAME --namespace=default -- python manage.py collectstatic --noinput

    - name: Notify deployment status
      if: always()
      run: |
        if [ "${{ job.status }}" == "success" ]; then
          echo "✅ Deployment successful!"
        else
          echo "❌ Deployment failed!"
        fi
```

### Advanced: Using OIDC (Recommended over Access Keys)

For better security, use OIDC instead of long-lived access keys:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v2
  with:
    role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/GitHubActionsRole
    role-session-name: GitHubActionsSession
    aws-region: ${{ env.AWS_REGION }}
```

**Setup OIDC trust relationship:**

```bash
# Create IAM OIDC identity provider for GitHub
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# Create IAM role with trust policy
cat > github-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_USERNAME/YOUR_REPO_NAME:*"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name GitHubActionsRole \
  --assume-role-policy-document file://github-trust-policy.json

# Attach necessary policies
aws iam attach-role-policy \
  --role-name GitHubActionsRole \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/GitHubActionsDeployPolicy
```

### Multi-Environment Deployment

Create separate workflows for different environments:

`.github/workflows/deploy-staging.yml`:
```yaml
name: Deploy to Staging

on:
  push:
    branches:
      - develop

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: backend-auth
  EKS_CLUSTER_NAME: staging-cluster
  NAMESPACE: staging
```

`.github/workflows/deploy-production.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main
    tags:
      - 'v*'

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: backend-auth
  EKS_CLUSTER_NAME: production-cluster
  NAMESPACE: production
```

---

## Troubleshooting

### Common Issues

#### 1. Container can't connect to RDS

**Symptoms:**
```
django.db.utils.OperationalError: connection to server at "xxx.xxx.xxx.xxx", port 5432 failed: timeout expired
```

**Solutions:**
- Check RDS security group allows inbound traffic from EKS nodes/pods
- Verify RDS is in the same VPC as EKS or VPC peering is configured
- Check RDS subnet group configuration
- Test connectivity: `kubectl run tmp --image=alpine --rm -it -- sh -c "apk add postgresql-client && psql -h HOST -U USER -d DB"`

#### 2. Can't retrieve secrets from AWS Secrets Manager

**Symptoms:**
```
botocore.exceptions.ClientError: An error occurred (AccessDeniedException) when calling the GetSecretValue operation
```

**Solutions:**
- Verify IAM role attached to Service Account has correct policy
- Check IRSA is properly configured: `kubectl describe sa backend-auth-sa`
- Verify pod has the annotation: `kubectl describe pod POD_NAME | grep AWS_ROLE_ARN`
- Test with AWS CLI: `kubectl exec POD -- aws secretsmanager get-secret-value --secret-id ecommerce2`

#### 3. Image pull errors from ECR

**Symptoms:**
```
Failed to pull image: authorization failed
```

**Solutions:**
- Ensure EKS nodes have IAM role with ECR permissions
- Check ECR repository policy allows EKS cluster
- Verify ECR repository exists and image was pushed

#### 4. Health check failures

**Symptoms:**
- Pods constantly restarting
- `CrashLoopBackOff` status

**Solutions:**
- Increase `initialDelaySeconds` in liveness/readiness probes
- Check application logs: `kubectl logs POD_NAME`
- Verify database migrations completed
- Check if static files are collected

#### 5. CORS issues

**Symptoms:**
- Frontend can't make requests to API
- CORS errors in browser console

**Solutions:**
- Update `ALLOWED_HOSTS` in Django settings
- Verify CORS middleware is properly configured
- Check if LoadBalancer/Ingress URL is in CORS allowed origins

### Debugging Commands

```bash
# View pod logs
kubectl logs -f deployment/backend-auth --namespace=default

# Get pod details
kubectl describe pod POD_NAME --namespace=default

# Execute command in pod
kubectl exec -it POD_NAME --namespace=default -- bash

# Check environment variables
kubectl exec POD_NAME --namespace=default -- env | grep AWS

# Test database connection
kubectl exec POD_NAME --namespace=default -- python manage.py dbshell

# Check secrets
kubectl get secrets --namespace=default
kubectl describe secret backend-auth-config --namespace=default

# View deployment status
kubectl rollout status deployment/backend-auth --namespace=default
kubectl get events --namespace=default --sort-by='.lastTimestamp'

# Scale deployment
kubectl scale deployment/backend-auth --replicas=5 --namespace=default

# Port forward for local testing
kubectl port-forward service/backend-auth-service 8000:80 --namespace=default
```

### Monitoring and Logging

#### Enable CloudWatch Container Insights

```bash
# Install CloudWatch agent
kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluentd-quickstart.yaml
```

#### View logs in CloudWatch

```bash
# Logs are automatically sent to CloudWatch Logs
# Log group: /aws/eks/CLUSTER_NAME/cluster
# Log stream: kubernetes.var.log.containers.backend-auth-*
```

---

## Best Practices

1. **Security**
   - Never commit secrets to Git
   - Use IRSA instead of hardcoded AWS credentials
   - Run containers as non-root user
   - Keep base images updated
   - Use least-privilege IAM policies

2. **Deployment**
   - Use semantic versioning for image tags
   - Implement blue-green or canary deployments
   - Set resource limits and requests
   - Configure horizontal pod autoscaling
   - Use liveness and readiness probes

3. **Monitoring**
   - Enable CloudWatch Container Insights
   - Set up alarms for pod failures
   - Monitor database connections
   - Track API response times
   - Log to centralized logging system

4. **Cost Optimization**
   - Use Spot instances for non-production
   - Right-size pod resources
   - Implement cluster autoscaler
   - Use ECR lifecycle policies

5. **CI/CD**
   - Run tests before deployment
   - Use separate environments (dev/staging/prod)
   - Implement approval gates for production
   - Tag releases with version numbers
   - Keep deployment rollback capability

---

## Additional Resources

- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Amazon ECR User Guide](https://docs.aws.amazon.com/ecr/)

---

## Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation
- Review CloudWatch logs
- Contact DevOps team

**Last Updated:** 2026-02-10
