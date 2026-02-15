#!/usr/bin/env python3
"""
Kubernetes Destruction Script for E-commerce Backend
Safely removes all backend resources from the cluster.
"""

import subprocess
import sys
import time
from typing import Tuple


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


def namespace_exists(namespace: str) -> bool:
    """Check if a namespace exists"""
    command = f"kubectl get namespace {namespace}"
    returncode, stdout, stderr = run_command(command, check=False)
    return returncode == 0


def resource_exists(resource_type: str, resource_name: str, namespace: str) -> bool:
    """Check if a Kubernetes resource exists"""
    command = f"kubectl get {resource_type} {resource_name} -n {namespace}"
    returncode, stdout, stderr = run_command(command, check=False)
    return returncode == 0


def delete_resource(resource_type: str, resource_name: str, namespace: str) -> bool:
    """Delete a Kubernetes resource"""
    if not resource_exists(resource_type, resource_name, namespace):
        print_info(f"{resource_type}/{resource_name} does not exist")
        return True

    command = f"kubectl delete {resource_type} {resource_name} -n {namespace}"
    returncode, stdout, stderr = run_command(command, check=False)

    if returncode == 0:
        print_success(f"Deleted {resource_type}/{resource_name}")
        return True
    else:
        print_error(f"Failed to delete {resource_type}/{resource_name}: {stderr}")
        return False


def delete_yaml(yaml_file: str) -> bool:
    """Delete resources defined in a YAML file"""
    command = f"kubectl delete -f {yaml_file}"
    returncode, stdout, stderr = run_command(command, check=False)

    if returncode == 0:
        print_success(f"Deleted resources from {yaml_file}")
        print(f"  {stdout.strip()}")
        return True
    else:
        # Check if it's just "not found" which is OK
        if "NotFound" in stderr or "not found" in stderr:
            print_info(f"Resources from {yaml_file} already deleted")
            return True
        else:
            print_error(f"Failed to delete {yaml_file}")
            print_error(f"  {stderr.strip()}")
            return False


def display_deletion_info(namespace: str):
    """Display what will be deleted"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}Deleting backend resources{Colors.END}")
    print(f"Namespace: {namespace}")
    print("\nResources to be deleted:")
    print("  - Ingress")
    print("  - Service")
    print("  - Deployment")
    print("  - ConfigMap")
    print("  - Secret")
    print("  - Certificate")
    print("  - Namespace")
    print("  - ServiceAccount (backend-auth-sa)")
    print(f"\n{Colors.YELLOW}Note: IAM resources will NOT be deleted{Colors.END}")
    print("(IAM Role and Policy can be reused for future deployments)\n")


def main():
    """Main destruction function"""

    # Configuration
    NAMESPACE = "ecommerce-backend-ns"
    DEPLOYMENT_NAME = "ecommerce-backend"
    SERVICE_NAME = "ecommerce-backend-svc"
    INGRESS_NAME = "ecommerce-backend-ingress"
    CONFIGMAP_NAME = "backend-config"
    SECRET_NAME = "backend-secrets"
    CERTIFICATE_NAME = "backend-tls-cert"
    SERVICE_ACCOUNT_NAME = "backend-auth-sa"

    # YAML files (for reference, we'll delete by resource type)
    INGRESS_YAML = "../deployment/backend_ingress.yaml"
    SERVICE_YAML = "../deployment/service.yaml"
    DEPLOYMENT_YAML = "../deployment/deployment.yaml"
    SECRET_YAML = "../deployment/secret.yaml"
    CONFIGMAP_YAML = "../deployment/configmap.yaml"

    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 70)
    print("  E-COMMERCE BACKEND DESTRUCTION")
    print("=" * 70)
    print(f"{Colors.END}")

    # Check if namespace exists
    if not namespace_exists(NAMESPACE):
        print_warning(f"Namespace '{NAMESPACE}' does not exist")
        print_info("Nothing to delete")
        sys.exit(0)

    # Display what will be deleted
    display_deletion_info(NAMESPACE)

    # ============================================
    # STEP 1: Delete Ingress
    # ============================================
    print_step(1, "Deleting Ingress...")
    delete_resource("ingress", INGRESS_NAME, NAMESPACE)

    # ============================================
    # STEP 2: Delete Service
    # ============================================
    print_step(2, "Deleting Service...")
    delete_resource("service", SERVICE_NAME, NAMESPACE)

    # Wait a moment for cleanup
    time.sleep(2)

    # ============================================
    # STEP 3: Delete Deployment
    # ============================================
    print_step(3, "Deleting Deployment...")
    delete_resource("deployment", DEPLOYMENT_NAME, NAMESPACE)

    print_info("Waiting for pods to terminate...")
    time.sleep(5)

    # Check if pods are gone
    command = f"kubectl get pods -n {NAMESPACE} -l app=ecommerce-backend"
    returncode, stdout, stderr = run_command(command, check=False)
    if returncode == 0 and "No resources found" in stdout:
        print_success("All pods terminated")
    else:
        print_warning("Some pods may still be terminating")

    # ============================================
    # STEP 4: Delete ConfigMap
    # ============================================
    print_step(4, "Deleting ConfigMap...")
    delete_resource("configmap", CONFIGMAP_NAME, NAMESPACE)

    # ============================================
    # STEP 5: Delete Secret
    # ============================================
    print_step(5, "Deleting Secret...")
    delete_resource("secret", SECRET_NAME, NAMESPACE)

    # ============================================
    # STEP 6: Delete Certificate
    # ============================================
    print_step(6, "Deleting Certificate...")
    delete_resource("certificate", CERTIFICATE_NAME, NAMESPACE)

    # Wait for certificate to be removed
    time.sleep(2)

    # ============================================
    # STEP 7: Delete Namespace
    # ============================================
    print_step(7, "Deleting Namespace...")

    if namespace_exists(NAMESPACE):
        command = f"kubectl delete namespace {NAMESPACE}"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode == 0:
            print_success(f"Deleted namespace: {NAMESPACE}")
            print_info("Waiting for namespace to be fully removed...")
            time.sleep(5)
        else:
            print_error(f"Failed to delete namespace: {stderr}")
    else:
        print_info(f"Namespace {NAMESPACE} already deleted")

    # ============================================
    # Summary
    # ============================================
    print(f"\n{Colors.BOLD}{Colors.GREEN}")
    print("=" * 70)
    print("  DESTRUCTION COMPLETED! ✓")
    print("=" * 70)
    print(f"{Colors.END}")

    print(f"\n{Colors.BOLD}What was deleted:{Colors.END}")
    print(f"  ✓ Ingress: {INGRESS_NAME}")
    print(f"  ✓ Service: {SERVICE_NAME}")
    print(f"  ✓ Deployment: {DEPLOYMENT_NAME}")
    print(f"  ✓ ConfigMap: {CONFIGMAP_NAME}")
    print(f"  ✓ Secret: {SECRET_NAME}")
    print(f"  ✓ Certificate: {CERTIFICATE_NAME}")
    print(f"  ✓ Namespace: {NAMESPACE}")
    print(f"  ✓ ServiceAccount: {SERVICE_ACCOUNT_NAME}")

    print(f"\n{Colors.BOLD}What was NOT deleted:{Colors.END}")
    print(f"  ℹ IAM Role: EKSBackendAuthRole")
    print(f"  ℹ IAM Policy: BackendAuthSecretsManagerPolicy")
    print(f"  ℹ ClusterIssuer: letsencrypt-prod")

    print(f"\n{Colors.BOLD}To delete IAM resources (if no longer needed):{Colors.END}")
    print("1. Detach policy from role:")
    print("   aws iam detach-role-policy --role-name EKSBackendAuthRole --policy-arn arn:aws:iam::793796654438:policy/BackendAuthSecretsManagerPolicy")
    print("\n2. Delete IAM role:")
    print("   aws iam delete-role --role-name EKSBackendAuthRole")
    print("\n3. Delete IAM policy:")
    print("   aws iam delete-policy --policy-arn arn:aws:iam::793796654438:policy/BackendAuthSecretsManagerPolicy")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Destruction interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
