#!/usr/bin/env python3
"""
Kubernetes Deployment Automation Script for E-commerce Backend
Automates the deployment process with namespace, secrets, ConfigMap, and ingress setup.
"""

import subprocess
import sys
import json
import time
from typing import Tuple, Optional


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_step(step_num: int, message: str):
    """Print a formatted step message"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}[STEP {step_num}]{Colors.END} {message}")


def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")


def print_warning(message: str):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")


def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def run_command(command: str, check: bool = True, capture_output: bool = True) -> Tuple[int, str, str]:
    """
    Run a shell command and return the result

    Args:
        command: Command to execute
        check: Whether to raise exception on non-zero exit
        capture_output: Whether to capture stdout/stderr

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout if e.stdout else "", e.stderr if e.stderr else ""


def check_kubectl():
    """Check if kubectl is installed and accessible"""
    print_info("Checking kubectl installation...")
    returncode, stdout, stderr = run_command("kubectl version --client --output=json", check=False)

    if returncode != 0:
        print_error("kubectl is not installed or not in PATH")
        print_error(f"Error: {stderr}")
        sys.exit(1)

    try:
        version_info = json.loads(stdout)
        client_version = version_info.get('clientVersion', {}).get('gitVersion', 'unknown')
        print_success(f"kubectl found (version: {client_version})")
    except json.JSONDecodeError:
        print_success("kubectl found")


def check_cluster_connection():
    """Check if we can connect to the Kubernetes cluster"""
    print_info("Checking cluster connection...")
    returncode, stdout, stderr = run_command("kubectl cluster-info", check=False)

    if returncode != 0:
        print_error("Cannot connect to Kubernetes cluster")
        print_error(f"Error: {stderr}")
        sys.exit(1)

    print_success("Connected to Kubernetes cluster")


def namespace_exists(namespace: str) -> bool:
    """Check if a namespace exists"""
    command = f"kubectl get namespace {namespace} --output=json"
    returncode, stdout, stderr = run_command(command, check=False)
    return returncode == 0


def resource_exists(resource_type: str, resource_name: str, namespace: str) -> bool:
    """Check if a Kubernetes resource exists"""
    command = f"kubectl get {resource_type} {resource_name} -n {namespace} --output=json"
    returncode, stdout, stderr = run_command(command, check=False)
    return returncode == 0


def apply_yaml(yaml_file: str, namespace: Optional[str] = None) -> bool:
    """Apply a Kubernetes YAML file"""
    namespace_flag = f"-n {namespace}" if namespace else ""
    command = f"kubectl apply -f {yaml_file} {namespace_flag}".strip()

    print_info(f"Applying {yaml_file}...")
    returncode, stdout, stderr = run_command(command, check=False)

    if returncode == 0:
        print_success(f"Applied {yaml_file}")
        print(f"  {stdout.strip()}")
        return True
    else:
        print_error(f"Failed to apply {yaml_file}")
        print_error(f"  {stderr.strip()}")
        return False


def wait_for_deployment(deployment_name: str, namespace: str, timeout: int = 300):
    """Wait for deployment to be ready"""
    print_info(f"Waiting for deployment '{deployment_name}' to be ready...")

    command = f"kubectl rollout status deployment/{deployment_name} -n {namespace} --timeout={timeout}s"
    returncode, stdout, stderr = run_command(command, check=False, capture_output=False)

    if returncode == 0:
        print_success(f"Deployment '{deployment_name}' is ready")
    else:
        print_warning(f"Deployment may not be fully ready. Check with: kubectl get pods -n {namespace}")


def get_pod_status(namespace: str):
    """Get pod status"""
    command = f"kubectl get pods -n {namespace}"
    returncode, stdout, stderr = run_command(command, check=False)

    if returncode == 0:
        print_info("Pod Status:")
        print(stdout)
    else:
        print_warning(f"Could not get pod status: {stderr}")


def get_service_endpoints(service_name: str, namespace: str):
    """Get service endpoints"""
    command = f"kubectl get svc {service_name} -n {namespace} -o jsonpath='{{.status.loadBalancer.ingress[0].hostname}}{{.status.loadBalancer.ingress[0].ip}}'"
    returncode, stdout, stderr = run_command(command, check=False)

    if returncode == 0 and stdout.strip():
        print_success(f"Service endpoint: {stdout.strip()}")
    else:
        command = f"kubectl get svc {service_name} -n {namespace}"
        returncode, stdout, stderr = run_command(command, check=False)
        if returncode == 0:
            print_info("Service created (ClusterIP - access via ingress)")


def get_ingress_info(ingress_name: str, namespace: str):
    """Get ingress information. Returns tuple of (hosts, protocol)"""
    # Check if TLS is configured
    command = f"kubectl get ingress {ingress_name} -n {namespace} -o jsonpath='{{.spec.tls}}'"
    returncode, tls_output, stderr = run_command(command, check=False)
    has_tls = returncode == 0 and tls_output.strip() and tls_output.strip() != "[]"
    protocol = "https" if has_tls else "http"

    # Get hosts
    command = f"kubectl get ingress {ingress_name} -n {namespace} -o jsonpath='{{range .spec.rules[*]}}{{.host}}{{\"\\n\"}}{{end}}'"
    returncode, stdout, stderr = run_command(command, check=False)

    if returncode == 0 and stdout.strip():
        hosts = [host.strip() for host in stdout.strip().split('\n') if host.strip()]
        if hosts:
            print_success("Ingress configured with hosts:")
            for host in hosts:
                print(f"  → {protocol}://{host}")
        return hosts, protocol
    return [], protocol


def main():
    """Main deployment automation function"""

    # Configuration
    NAMESPACE = "ecommerce-backend-ns"
    DEPLOYMENT_NAME = "ecommerce-backend"
    SERVICE_NAME = "ecommerce-backend-svc"
    INGRESS_NAME = "ecommerce-backend-ingress"

    # YAML files (relative to automation_script/)
    NAMESPACE_YAML = "../deployment/namespace.yaml"
    CLUSTERISSUER_YAML = "../deployment/clusterissuer.yaml"
    CERTIFICATE_YAML = "../deployment/certificate.yaml"
    CONFIGMAP_YAML = "../deployment/configmap.yaml"
    SECRET_YAML = "../deployment/secret.yaml"
    DEPLOYMENT_YAML = "../deployment/deployment.yaml"
    SERVICE_YAML = "../deployment/service.yaml"
    INGRESS_YAML = "../deployment/backend_ingress.yaml"

    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  E-COMMERCE BACKEND DEPLOYMENT AUTOMATION")
    print("=" * 70)
    print(f"{Colors.END}")

    # Pre-flight checks
    check_kubectl()
    check_cluster_connection()

    # ============================================
    # STEP 1: Create or verify namespace
    # ============================================
    print_step(1, f"Creating/verifying namespace '{NAMESPACE}'...")

    if not namespace_exists(NAMESPACE):
        print_info(f"Namespace '{NAMESPACE}' does not exist, creating...")
        if not apply_yaml(NAMESPACE_YAML):
            print_error("Failed to create namespace. Exiting.")
            sys.exit(1)
        time.sleep(2)
    else:
        print_success(f"Namespace '{NAMESPACE}' already exists")

    # ============================================
    # STEP 2: Apply ClusterIssuer
    # ============================================
    print_step(2, "Applying ClusterIssuer...")

    # Check if ClusterIssuer already exists
    command = "kubectl get clusterissuer letsencrypt-prod"
    returncode, _, _ = run_command(command, check=False)

    if returncode == 0:
        print_success("ClusterIssuer 'letsencrypt-prod' already exists")
    else:
        if not apply_yaml(CLUSTERISSUER_YAML):
            print_warning("Failed to apply ClusterIssuer. Continuing anyway...")
        else:
            time.sleep(2)

    # ============================================
    # STEP 3: Apply Certificate
    # ============================================
    print_step(3, "Applying Certificate...")

    if not apply_yaml(CERTIFICATE_YAML):
        print_warning("Failed to apply Certificate. Continuing anyway...")
    else:
        print_info("Certificate requested. It may take a few minutes to be issued.")
        time.sleep(3)

    # ============================================
    # STEP 4: Apply ConfigMap
    # ============================================
    print_step(4, "Applying ConfigMap...")

    if not apply_yaml(CONFIGMAP_YAML):
        print_error("Failed to apply ConfigMap. Exiting.")
        sys.exit(1)

    # ============================================
    # STEP 5: Verify/Apply Secret
    # ============================================
    print_step(5, "Verifying Secret...")

    # Check if secret already exists in cluster (CI/CD mode)
    command = f"kubectl get secret backend-secrets -n {NAMESPACE}"
    returncode, _, _ = run_command(command, check=False)

    if returncode == 0:
        print_success("Secret 'backend-secrets' already exists in cluster")
        print_info("Skipping secret.yaml application (CI/CD mode)")
    else:
        # Secret doesn't exist, try to apply from file (local mode)
        import os
        if os.path.exists(SECRET_YAML):
            print_info("Applying secret from secret.yaml (local mode)")
            if not apply_yaml(SECRET_YAML):
                print_error("Failed to apply Secret. Exiting.")
                sys.exit(1)
        else:
            print_error("Secret 'backend-secrets' not found in cluster!")
            print_error("And secret.yaml not found locally!")
            print_error("")
            print_error("For local deployment:")
            print_error(f"  1. Create secret.yaml from template:")
            print_error(f"     cp {SECRET_YAML}.template {SECRET_YAML}")
            print_error(f"  2. Edit and add your SECRET_KEY")
            print_error("")
            print_error("Or create secret directly in cluster:")
            print_error(f"  kubectl create secret generic backend-secrets \\")
            print_error(f"    --from-literal=SECRET_KEY=<your-key> \\")
            print_error(f"    -n {NAMESPACE}")
            sys.exit(1)

    # Wait for resources to be ready
    time.sleep(2)

    # ============================================
    # STEP 6: Apply Deployment
    # ============================================
    print_step(6, "Applying Deployment...")

    if not apply_yaml(DEPLOYMENT_YAML):
        print_error("Failed to apply Deployment. Exiting.")
        sys.exit(1)

    # ============================================
    # STEP 7: Apply Service
    # ============================================
    print_step(7, "Applying Service...")

    if not apply_yaml(SERVICE_YAML):
        print_error("Failed to apply Service. Exiting.")
        sys.exit(1)

    # ============================================
    # STEP 8: Apply Ingress
    # ============================================
    print_step(8, "Applying Ingress...")

    if not apply_yaml(INGRESS_YAML):
        print_warning("Failed to apply Ingress. Continuing anyway...")

    # Wait for resources to be created
    time.sleep(3)

    # ============================================
    # STEP 9: Wait for deployment to be ready
    # ============================================
    print_step(9, "Waiting for deployment to be ready...")

    wait_for_deployment(DEPLOYMENT_NAME, NAMESPACE, timeout=300)

    # ============================================
    # STEP 10: Get deployment status
    # ============================================
    print_step(10, "Checking deployment status...")

    get_pod_status(NAMESPACE)

    # ============================================
    # STEP 11: Get service and ingress info
    # ============================================
    print_step(11, "Retrieving service and ingress information...")

    get_service_endpoints(SERVICE_NAME, NAMESPACE)
    hosts, protocol = get_ingress_info(INGRESS_NAME, NAMESPACE)

    # ============================================
    # Summary
    # ============================================
    print(f"\n{Colors.BOLD}{Colors.GREEN}")
    print("=" * 70)
    print("  DEPLOYMENT COMPLETED! 🎉")
    print("=" * 70)
    print(f"{Colors.END}")

    print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
    print("1. Check pod logs:")
    print(f"   kubectl logs -f deployment/{DEPLOYMENT_NAME} -n {NAMESPACE}")
    print("\n2. Check pod status:")
    print(f"   kubectl get pods -n {NAMESPACE}")
    print("\n3. Describe pod for events:")
    print(f"   kubectl describe pod -l app=ecommerce-backend -n {NAMESPACE}")
    print("\n4. Test the API endpoints:")
    if hosts:
        for host in hosts:
            print(f"   curl {protocol}://{host}/api/auth/login")

    print(f"\n{Colors.BOLD}Troubleshooting:{Colors.END}")
    print("- If pods are not starting, check logs:")
    print(f"  kubectl logs <pod-name> -n {NAMESPACE}")
    print("- If database connection fails, check RDS security group")
    print("- If secrets access fails, verify IRSA setup:")
    print("  kubectl describe sa backend-auth-sa -n ecommerce")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Deployment interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
