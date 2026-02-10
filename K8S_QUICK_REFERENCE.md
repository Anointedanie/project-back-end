# Kubernetes Quick Reference

## Build & Deploy

```bash
# Build Docker image
export DOCKER_REGISTRY="your-registry"
./build-docker.sh v1.0.0

# Push to registry
docker push ${DOCKER_REGISTRY}/django-ecommerce:v1.0.0

# Deploy to Kubernetes
kubectl apply -f k8s-deployment.yaml

# Check deployment status
kubectl get pods -n ecommerce -w
```

## Common Commands

```bash
# View all resources
kubectl get all -n ecommerce

# Check pod logs (follow)
kubectl logs -f deployment/django-app -n ecommerce

# Execute commands in pod
kubectl exec -it <pod-name> -n ecommerce -- bash

# Run Django management commands
kubectl exec -it <pod-name> -n ecommerce -- python manage.py migrate
kubectl exec -it <pod-name> -n ecommerce -- python manage.py createsuperuser
kubectl exec -it <pod-name> -n ecommerce -- python manage.py collectstatic

# Port forward for local testing
kubectl port-forward svc/django-service 8000:8000 -n ecommerce

# Scale deployment
kubectl scale deployment django-app --replicas=5 -n ecommerce

# Check HPA status
kubectl get hpa -n ecommerce

# View pod resource usage
kubectl top pods -n ecommerce
```

## Troubleshooting

```bash
# Describe pod (see events)
kubectl describe pod -l app=django -n ecommerce

# View pod logs (last 100 lines)
kubectl logs -l app=django -n ecommerce --tail=100

# View previous logs (if pod crashed)
kubectl logs <pod-name> -n ecommerce --previous

# Check environment variables
kubectl exec -it <pod-name> -n ecommerce -- env | grep -E "AWS_|DB_"

# Test AWS Secrets Manager connection
kubectl exec -it <pod-name> -n ecommerce -- python test_aws_secrets.py

# Get a shell in the pod
kubectl exec -it <pod-name> -n ecommerce -- /bin/bash

# Test database connection
kubectl exec -it <pod-name> -n ecommerce -- python manage.py dbshell
```

## Rolling Updates

```bash
# Update image
kubectl set image deployment/django-app \
  django=${DOCKER_REGISTRY}/django-ecommerce:v1.0.1 \
  -n ecommerce

# Check rollout status
kubectl rollout status deployment/django-app -n ecommerce

# View rollout history
kubectl rollout history deployment/django-app -n ecommerce

# Rollback to previous version
kubectl rollout undo deployment/django-app -n ecommerce

# Rollback to specific revision
kubectl rollout undo deployment/django-app --to-revision=2 -n ecommerce
```

## Configuration Updates

```bash
# Edit ConfigMap
kubectl edit configmap django-config -n ecommerce

# Edit Secret
kubectl edit secret django-secrets -n ecommerce

# Restart deployment (to pick up config changes)
kubectl rollout restart deployment/django-app -n ecommerce
```

## Debugging

```bash
# Get pod name
POD_NAME=$(kubectl get pods -n ecommerce -l app=django -o jsonpath='{.items[0].metadata.name}')

# View all pod details
kubectl describe pod $POD_NAME -n ecommerce

# Check pod events
kubectl get events -n ecommerce --sort-by='.lastTimestamp'

# Check service endpoints
kubectl get endpoints django-service -n ecommerce

# Test service connectivity from another pod
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n ecommerce -- \
  curl -v http://django-service:8000/admin/
```

## Cleanup

```bash
# Delete deployment only
kubectl delete deployment django-app -n ecommerce

# Delete all resources from manifest
kubectl delete -f k8s-deployment.yaml

# Delete entire namespace
kubectl delete namespace ecommerce
```

## AWS/EKS Specific

```bash
# Check service account IAM role
kubectl describe sa django-app -n ecommerce

# Get AWS credentials from pod
kubectl exec -it <pod-name> -n ecommerce -- env | grep AWS

# Test IAM role permissions
kubectl exec -it <pod-name> -n ecommerce -- \
  aws sts get-caller-identity

# List secrets in AWS Secrets Manager
kubectl exec -it <pod-name> -n ecommerce -- \
  aws secretsmanager list-secrets --region us-east-1
```

## Ingress

```bash
# Get ingress details
kubectl get ingress -n ecommerce
kubectl describe ingress django-ingress -n ecommerce

# Get LoadBalancer IP
kubectl get svc -n ingress-nginx ingress-nginx-controller

# Check SSL certificate
kubectl get certificate -n ecommerce
kubectl describe certificate django-tls -n ecommerce
```

## Monitoring

```bash
# Watch pod status
watch kubectl get pods -n ecommerce

# Monitor HPA
watch kubectl get hpa -n ecommerce

# View resource usage
kubectl top nodes
kubectl top pods -n ecommerce --containers
```
