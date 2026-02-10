#!/bin/bash
set -e

# Configuration
IMAGE_NAME="django-ecommerce"
IMAGE_TAG="${1:-latest}"
REGISTRY="${DOCKER_REGISTRY:-your-registry}"  # Set DOCKER_REGISTRY env var or pass as argument

echo "Building Docker image..."
echo "  Image: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

# Build the image
docker build -t ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} .

echo "✅ Build complete!"
echo ""
echo "To push to registry:"
echo "  docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "To run locally:"
echo "  docker run -p 8000:8000 --env-file .env ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "To test the image:"
echo "  docker run --rm ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} python manage.py check"
