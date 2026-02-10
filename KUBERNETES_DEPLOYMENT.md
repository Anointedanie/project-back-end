# Kubernetes Deployment Guide

This guide covers deploying the Django e-commerce application to a Kubernetes cluster with AWS RDS and Secrets Manager integration.

## Prerequisites

- Kubernetes cluster (EKS, GKE, or any K8s cluster)
- `kubectl` configured to access your cluster
- Docker registry access (Docker Hub, ECR, GCR, etc.)
- AWS RDS PostgreSQL database running
- AWS Secrets Manager with "ecommerce2" secret configured
- AWS IAM permissions for Secrets Manager access

## Overview

The application uses:
- **Django** with Django REST Framework
- **Gunicorn** as the WSGI server
- **PostgreSQL** on AWS RDS
- **AWS Secrets Manager** for credential management via boto3
- **Kubernetes** for orchestration

## Step 1: Build and Push Docker Image

### Build the image

```bash
# Make the build script executable
chmod +x build-docker.sh

# Build the image (replace with your registry)
export DOCKER_REGISTRY="your-ecr-registry.amazonaws.com"
./build-docker.sh v1.0.0
```

### Push to your registry

```bash
# For AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ${DOCKER_REGISTRY}
docker push ${DOCKER_REGISTRY}/django-ecommerce:v1.0.0

# For Docker Hub
docker login
docker tag ${DOCKER_REGISTRY}/django-ecommerce:v1.0.0 yourusername/django-ecommerce:v1.0.0
docker push yourusername/django-ecommerce:v1.0.0
```

## Step 2: Configure AWS IAM (for EKS)

### Option A: Using IAM Roles for Service Accounts (IRSA) - Recommended for EKS

1. **Create IAM policy** for Secrets Manager access:

```bash
aws iam create-policy \
  --policy-name EcommerceSecretsManagerPolicy \
  --policy-document file://iam_policy_for_secrets_manager.json
```

2. **Create IAM role** for the service account:

```bash
eksctl create iamserviceaccount \
  --name django-app \
  --namespace ecommerce \
  --cluster your-cluster-name \
  --attach-policy-arn arn:aws:iam::793796654438:policy/EcommerceSecretsManagerPolicy \
  --approve \
  --override-existing-serviceaccounts
```

3. **Update k8s-deployment.yaml** with the correct role ARN in the ServiceAccount annotation.

### Option B: Using EC2 Instance Profile (for self-managed K8s on EC2)

Attach the IAM policy to your EC2 instance role that runs the Kubernetes nodes.

### Option C: Using AWS Access Keys (Not recommended for production)

Store AWS credentials in Kubernetes secrets:

```bash
kubectl create secret generic aws-credentials \
  --from-literal=AWS_ACCESS_KEY_ID=your-access-key \
  --from-literal=AWS_SECRET_ACCESS_KEY=your-secret-key \
  --namespace ecommerce
```

Then add these to the deployment's `envFrom` section.

## Step 3: Update Kubernetes Manifests

Edit `k8s-deployment.yaml`:

1. **Update image name** in Deployment (line ~140):
   ```yaml
   image: your-registry/django-ecommerce:v1.0.0
   ```

2. **Update ALLOWED_HOSTS** in ConfigMap:
   ```yaml
   ALLOWED_HOSTS: "your-domain.com,api.your-domain.com"
   ```

3. **Update CORS_ALLOWED_ORIGINS** in ConfigMap:
   ```yaml
   CORS_ALLOWED_ORIGINS: "https://your-frontend.com"
   ```

4. **Generate new SECRET_KEY** in Secret:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

5. **Update Ingress hostname** (if using):
   ```yaml
   host: api.your-domain.com
   ```

6. **Update IAM role ARN** in ServiceAccount annotation (if using IRSA):
   ```yaml
   eks.amazonaws.com/role-arn: arn:aws:iam::793796654438:role/ecommerce-django-role
   ```

## Step 4: Deploy to Kubernetes

### Create namespace and resources

```bash
# Apply all resources
kubectl apply -f k8s-deployment.yaml

# Verify deployment
kubectl get all -n ecommerce

# Check pod logs
kubectl logs -f deployment/django-app -n ecommerce

# Check pod status
kubectl describe pod -l app=django -n ecommerce
```

### Run database migrations (if not using init container)

```bash
# Get a pod name
POD_NAME=$(kubectl get pods -n ecommerce -l app=django -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec -it $POD_NAME -n ecommerce -- python manage.py migrate

# Create superuser (optional)
kubectl exec -it $POD_NAME -n ecommerce -- python manage.py createsuperuser
```

## Step 5: Verify Deployment

### Check service endpoints

```bash
# Port-forward to test locally
kubectl port-forward svc/django-service 8000:8000 -n ecommerce

# Test the API
curl http://localhost:8000/admin/
curl http://localhost:8000/api/auth/login/
```

### Check logs for AWS Secrets Manager connection

```bash
kubectl logs -f deployment/django-app -n ecommerce | grep -i "secrets\|aws\|database"
```

You should see:
```
Loading database credentials from AWS Secrets Manager
Successfully retrieved secret
Database configuration ready
```

## Step 6: Configure Ingress (Optional)

If you're using an Ingress controller:

### Install NGINX Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

### Install cert-manager for SSL

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml
```

### Configure DNS

Point your domain to the Ingress LoadBalancer IP:

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

## Scaling

### Manual scaling

```bash
kubectl scale deployment django-app --replicas=5 -n ecommerce
```

### Auto-scaling

The HPA (HorizontalPodAutoscaler) is included in the manifest and will automatically scale based on CPU/memory usage.

```bash
# Check HPA status
kubectl get hpa -n ecommerce
```

## Troubleshooting

### Pods not starting

```bash
# Check pod events
kubectl describe pod -l app=django -n ecommerce

# Check logs
kubectl logs -l app=django -n ecommerce --tail=100
```

### Database connection issues

```bash
# Verify secrets are mounted
kubectl exec -it <pod-name> -n ecommerce -- env | grep -E "AWS_|DB_"

# Test database connection
kubectl exec -it <pod-name> -n ecommerce -- python manage.py dbshell
```

### AWS Secrets Manager access issues

```bash
# Check service account annotation
kubectl describe sa django-app -n ecommerce

# Verify IAM role
aws sts assume-role --role-arn arn:aws:iam::793796654438:role/ecommerce-django-role --role-session-name test

# Test from inside pod
kubectl exec -it <pod-name> -n ecommerce -- python test_aws_secrets.py
```

### View all resources

```bash
kubectl get all,configmap,secret,ingress,hpa -n ecommerce
```

## Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Django secret key | Yes | - |
| `DEBUG` | Enable debug mode | No | False |
| `ALLOWED_HOSTS` | Comma-separated hostnames | Yes | - |
| `USE_AWS_SECRETS` | Use AWS Secrets Manager | Yes | True |
| `AWS_SECRET_NAME` | Secret name in AWS | Yes | ecommerce2 |
| `AWS_REGION` | AWS region | Yes | us-east-1 |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | Yes | - |
| `JWT_ACCESS_TOKEN_LIFETIME` | JWT access token lifetime (minutes) | No | 60 |
| `JWT_REFRESH_TOKEN_LIFETIME` | JWT refresh token lifetime (minutes) | No | 1440 |
| `RUN_MIGRATIONS` | Run migrations on startup | No | true |
| `COLLECT_STATIC` | Collect static files on startup | No | true |
| `WAIT_FOR_DB` | Wait for database on startup | No | true |

## Security Checklist

- [ ] Changed `SECRET_KEY` to a unique value
- [ ] Set `DEBUG=False` in production
- [ ] Configured proper `ALLOWED_HOSTS`
- [ ] Using HTTPS/TLS (Ingress with cert-manager)
- [ ] IAM roles properly configured (least privilege)
- [ ] Database credentials stored in AWS Secrets Manager
- [ ] Running containers as non-root user
- [ ] Resource limits set on pods
- [ ] Network policies configured (optional)
- [ ] Regular security updates applied

## Monitoring and Logging

### View application logs

```bash
# Stream logs
kubectl logs -f deployment/django-app -n ecommerce

# View logs from all pods
kubectl logs -l app=django -n ecommerce --tail=100

# View previous container logs (if crashed)
kubectl logs <pod-name> -n ecommerce --previous
```

### Monitor pod health

```bash
# Watch pod status
kubectl get pods -n ecommerce -w

# Check pod resource usage
kubectl top pods -n ecommerce
```

## Updating the Application

```bash
# Build new version
./build-docker.sh v1.0.1

# Push to registry
docker push ${DOCKER_REGISTRY}/django-ecommerce:v1.0.1

# Update deployment
kubectl set image deployment/django-app django=${DOCKER_REGISTRY}/django-ecommerce:v1.0.1 -n ecommerce

# Watch rollout status
kubectl rollout status deployment/django-app -n ecommerce

# Rollback if needed
kubectl rollout undo deployment/django-app -n ecommerce
```

## Cleanup

```bash
# Delete all resources
kubectl delete -f k8s-deployment.yaml

# Delete namespace (will delete everything in it)
kubectl delete namespace ecommerce
```

## Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [AWS IAM Roles for Service Accounts](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/configure.html)
