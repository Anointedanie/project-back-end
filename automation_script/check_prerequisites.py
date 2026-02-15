#!/usr/bin/env python3
"""
Prerequisites Checker for E-commerce Backend Deployment
Verifies all required tools, configurations, and AWS resources are available.
"""

import subprocess
import sys
import json
from typing import Tuple, List, Dict


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


def print_section(message: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{message}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")


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


class PrerequisiteChecker:
    """Check all prerequisites for deployment"""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0
        self.config = {
            'cluster_name': 'ecommerce-eks',
            'region': 'us-east-1',
            'account_id': '793796654438',
            'namespace': 'ecommerce-backend-ns',
            'secret_name': 'ecommerce2',
        }

    def check_kubectl(self) -> bool:
        """Check if kubectl is installed"""
        print_info("Checking kubectl installation...")

        returncode, stdout, stderr = run_command("kubectl version --client --output=json", check=False)

        if returncode != 0:
            print_error("kubectl is not installed or not in PATH")
            print_info("Install from: https://kubernetes.io/docs/tasks/tools/")
            return False

        try:
            version_info = json.loads(stdout)
            version = version_info.get('clientVersion', {}).get('gitVersion', 'unknown')
            print_success(f"kubectl installed (version: {version})")
            return True
        except json.JSONDecodeError:
            print_success("kubectl installed")
            return True

    def install_aws_cli(self) -> bool:
        """Install AWS CLI automatically"""
        print_info("Installing AWS CLI...")

        # Download AWS CLI installer
        print_info("  Downloading AWS CLI installer...")
        download_cmd = 'curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"'
        returncode, _, stderr = run_command(download_cmd, check=False)
        if returncode != 0:
            print_error(f"Failed to download AWS CLI: {stderr}")
            return False

        # Install unzip if needed
        print_info("  Ensuring unzip is installed...")
        returncode, _, _ = run_command("which unzip", check=False)
        if returncode != 0:
            run_command("sudo apt-get install -y unzip", check=False)

        # Unzip the installer
        print_info("  Extracting AWS CLI installer...")
        returncode, _, stderr = run_command("unzip -q -o /tmp/awscliv2.zip -d /tmp/", check=False)
        if returncode != 0:
            print_error(f"Failed to extract AWS CLI: {stderr}")
            return False

        # Install AWS CLI
        print_info("  Installing AWS CLI...")
        returncode, _, stderr = run_command("sudo /tmp/aws/install --update", check=False)
        if returncode != 0:
            print_error(f"Failed to install AWS CLI: {stderr}")
            return False

        # Cleanup
        run_command("rm -rf /tmp/awscliv2.zip /tmp/aws", check=False)

        print_success("AWS CLI installed successfully")
        return True

    def check_aws_cli(self) -> bool:
        """Check if AWS CLI is installed"""
        print_info("Checking AWS CLI installation...")

        returncode, stdout, stderr = run_command("aws --version", check=False)

        if returncode != 0:
            print_warning("AWS CLI is not installed")
            print_info("Attempting to install AWS CLI...")
            if self.install_aws_cli():
                # Re-check after installation
                returncode, stdout, _ = run_command("aws --version", check=False)
                if returncode == 0:
                    print_success(f"AWS CLI installed ({stdout.strip()})")
                    return True
            print_error("Failed to install AWS CLI")
            return False

        print_success(f"AWS CLI installed ({stdout.strip()})")
        return True

    def install_docker(self) -> bool:
        """Install Docker automatically"""
        print_info("Installing Docker...")

        # Check if running on Ubuntu/Debian
        returncode, _, _ = run_command("which apt-get", check=False)
        if returncode != 0:
            print_error("This script requires Ubuntu/Debian with apt-get")
            print_info("Please install Docker manually from: https://docs.docker.com/get-docker/")
            return False

        # Update package list
        print_info("  Updating package list...")
        run_command("sudo apt-get update -qq", check=False)

        # Install prerequisites
        print_info("  Installing prerequisites...")
        prereq_cmd = (
            "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "
            "ca-certificates curl gnupg lsb-release"
        )
        returncode, _, stderr = run_command(prereq_cmd, check=False)
        if returncode != 0:
            print_error(f"Failed to install prerequisites: {stderr}")
            return False

        # Add Docker's official GPG key
        print_info("  Adding Docker GPG key...")
        gpg_cmd = (
            "sudo mkdir -p /etc/apt/keyrings && "
            "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | "
            "sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes"
        )
        run_command(gpg_cmd, check=False)

        # Set up Docker repository
        print_info("  Setting up Docker repository...")
        repo_cmd = (
            'echo "deb [arch=$(dpkg --print-architecture) '
            'signed-by=/etc/apt/keyrings/docker.gpg] '
            'https://download.docker.com/linux/ubuntu '
            '$(lsb_release -cs) stable" | '
            'sudo tee /etc/apt/sources.list.d/docker.list > /dev/null'
        )
        run_command(repo_cmd, check=False)

        # Update package list again
        print_info("  Updating package list...")
        run_command("sudo apt-get update -qq", check=False)

        # Install Docker
        print_info("  Installing Docker Engine...")
        install_cmd = (
            "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "
            "docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"
        )
        returncode, _, stderr = run_command(install_cmd, check=False)
        if returncode != 0:
            print_error(f"Failed to install Docker: {stderr}")
            return False

        # Start Docker service
        print_info("  Starting Docker service...")
        run_command("sudo systemctl start docker", check=False)
        run_command("sudo systemctl enable docker", check=False)

        print_success("Docker installed successfully")
        return True

    def check_docker(self) -> bool:
        """Check if Docker is installed"""
        print_info("Checking Docker installation...")

        returncode, stdout, stderr = run_command("docker --version", check=False)

        if returncode != 0:
            print_warning("Docker is not installed")
            print_info("Attempting to install Docker...")
            if self.install_docker():
                # Re-check after installation
                returncode, stdout, _ = run_command("docker --version", check=False)
                if returncode == 0:
                    print_success(f"Docker installed ({stdout.strip()})")
                    return True
            print_error("Failed to install Docker")
            return False

        print_success(f"Docker installed ({stdout.strip()})")

        # Check if Docker daemon is running
        returncode, _, _ = run_command("docker info", check=False)
        if returncode != 0:
            print_warning("Docker daemon not running - starting...")
            returncode, _, _ = run_command("sudo systemctl start docker", check=False)
            if returncode == 0:
                print_success("Docker daemon started")
            else:
                print_warning("Failed to start Docker daemon")
                print_info("Start manually: sudo systemctl start docker")

        return True

    def check_aws_credentials(self) -> bool:
        """Check if AWS credentials are configured"""
        print_info("Checking AWS credentials...")

        returncode, stdout, stderr = run_command("aws sts get-caller-identity", check=False)

        if returncode != 0:
            print_error("AWS credentials not configured")
            print_info("Run: aws configure")
            return False

        try:
            identity = json.loads(stdout)
            account = identity.get('Account', 'unknown')
            arn = identity.get('Arn', 'unknown')
            print_success(f"AWS credentials configured")
            print(f"  Account: {account}")
            print(f"  ARN: {arn}")

            if account != self.config['account_id']:
                print_warning(f"Account ID mismatch! Expected: {self.config['account_id']}, Got: {account}")
                self.warnings += 1

            return True
        except json.JSONDecodeError:
            print_error("Could not parse AWS identity")
            return False

    def check_cluster_connection(self) -> bool:
        """Check if we can connect to the Kubernetes cluster"""
        print_info("Checking Kubernetes cluster connection...")

        returncode, stdout, stderr = run_command("kubectl cluster-info", check=False)

        if returncode != 0:
            print_warning("Cannot connect to Kubernetes cluster")
            print_info("Attempting to configure kubeconfig...")

            # Try to configure kubeconfig automatically
            config_cmd = f"aws eks update-kubeconfig --name {self.config['cluster_name']} --region {self.config['region']}"
            returncode, stdout, stderr = run_command(config_cmd, check=False)

            if returncode != 0:
                print_error("Failed to configure kubeconfig")
                print_error(f"  {stderr.strip()}")
                print_info(f"Configure manually: {config_cmd}")
                return False

            print_success("Kubeconfig configured successfully")

            # Verify connection now works
            returncode, stdout, stderr = run_command("kubectl cluster-info", check=False)
            if returncode != 0:
                print_error("Still cannot connect to cluster after configuring kubeconfig")
                return False

            print_success("Connected to Kubernetes cluster")
            return True

        print_success("Connected to Kubernetes cluster")
        return True

    def check_namespace(self) -> bool:
        """Check if the namespace exists"""
        print_info(f"Checking namespace '{self.config['namespace']}'...")

        command = f"kubectl get namespace {self.config['namespace']}"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode != 0:
            print_warning(f"Namespace '{self.config['namespace']}' does not exist")
            print_info("Will be created during deployment by deploy_backend.py")
            print_info("Or run: ./setup_irsa.py to create it with IRSA setup")
            self.warnings += 1
            return True  # Return True as it's not a blocker

        print_success(f"Namespace '{self.config['namespace']}' exists")
        return True

    def check_service_account(self) -> bool:
        """Check if the service account exists"""
        print_info("Checking service account 'backend-auth-sa'...")

        command = f"kubectl get sa backend-auth-sa -n {self.config['namespace']}"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode != 0:
            print_warning("Service account 'backend-auth-sa' does not exist")
            print_info("Create with: ./setup_irsa.py")
            self.warnings += 1
            return True  # Return True as it's not a blocker

        # Check for IAM role annotation
        command = f"kubectl get sa backend-auth-sa -n {self.config['namespace']} -o jsonpath='{{.metadata.annotations.eks\\.amazonaws\\.com/role-arn}}'"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode == 0 and stdout.strip():
            print_success(f"Service account exists with IAM role")
            print(f"  Role ARN: {stdout.strip()}")
            return True
        else:
            print_warning("Service account exists but no IAM role annotation found")
            print_info("Configure IRSA with: ./setup_irsa.py")
            self.warnings += 1
            return True  # Return True as it can be fixed later

    def check_secrets_manager(self) -> bool:
        """Check if the secret exists in AWS Secrets Manager"""
        print_info(f"Checking AWS Secrets Manager secret '{self.config['secret_name']}'...")

        command = f"aws secretsmanager describe-secret --secret-id {self.config['secret_name']} --region {self.config['region']}"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode != 0:
            print_error(f"Secret '{self.config['secret_name']}' not found in Secrets Manager")
            print_info("Create the secret with database credentials")
            return False

        try:
            secret_info = json.loads(stdout)
            secret_name = secret_info.get('Name', 'unknown')
            kms_key = secret_info.get('KmsKeyId', 'default')
            print_success(f"Secret '{secret_name}' exists")
            print(f"  KMS Key: {kms_key}")
            return True
        except json.JSONDecodeError:
            print_warning("Could not parse secret information")
            self.warnings += 1
            return False

    def check_iam_role(self) -> bool:
        """Check if the IAM role exists"""
        print_info("Checking IAM role 'EKSBackendAuthRole'...")

        command = "aws iam get-role --role-name EKSBackendAuthRole"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode != 0:
            print_warning("IAM role 'EKSBackendAuthRole' does not exist")
            print_info("Create with: ./setup_irsa.py")
            self.warnings += 1
            return False

        print_success("IAM role 'EKSBackendAuthRole' exists")
        return True

    def check_ecr_repository(self) -> bool:
        """Check if ECR repository exists and has images"""
        print_info("Checking ECR repository...")

        repo_name = "ecommerce/backend"
        command = f"aws ecr describe-repositories --repository-names {repo_name} --region {self.config['region']}"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode != 0:
            print_warning(f"ECR repository '{repo_name}' does not exist")
            print_info(f"Create with: aws ecr create-repository --repository-name {repo_name} --region {self.config['region']}")
            self.warnings += 1
            return False

        # Check for images
        command = f"aws ecr list-images --repository-name {repo_name} --region {self.config['region']}"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode == 0:
            try:
                images = json.loads(stdout)
                image_count = len(images.get('imageIds', []))
                if image_count > 0:
                    print_success(f"ECR repository exists with {image_count} images")
                else:
                    print_warning(f"ECR repository exists but has no images")
                    self.warnings += 1
                return True
            except json.JSONDecodeError:
                print_warning("Could not parse ECR images")
                self.warnings += 1
                return False

        return True

    def install_nginx_ingress(self) -> bool:
        """Install nginx ingress controller with AWS Load Balancer Controller"""
        print_info("Installing Nginx Ingress Controller...")

        import time

        # Step 1: Apply AWS Load Balancer Controller Service Account
        print_info("  Step 1/3: Applying AWS Load Balancer Controller Service Account...")
        sa_file = "../deployment/aws-load-balancer-controller-sa.yaml"
        returncode, _, stderr = run_command(f"kubectl apply -f {sa_file}", check=False)
        if returncode != 0:
            print_error(f"Failed to apply service account: {stderr}")
            return False
        print_success("  Service account applied")

        # Wait a moment for service account to be created
        time.sleep(2)

        # Step 2: Apply AWS Load Balancer Controller
        print_info("  Step 2/3: Applying AWS Load Balancer Controller...")
        lb_file = "../deployment/aws_lb_controller.yaml"
        returncode, _, stderr = run_command(f"kubectl apply -f {lb_file}", check=False)
        if returncode != 0:
            print_error(f"Failed to apply AWS LB controller: {stderr}")
            return False
        print_success("  AWS Load Balancer Controller applied")

        # Wait for AWS LB controller to be ready
        print_info("  Waiting for AWS Load Balancer Controller to be ready...")
        time.sleep(5)

        # Step 3: Apply Nginx Ingress with NLB
        print_info("  Step 3/3: Applying Nginx Ingress Controller with NLB...")
        ingress_file = "../deployment/nginx-ingress-nlb.yaml"
        returncode, _, stderr = run_command(f"kubectl apply -f {ingress_file}", check=False)
        if returncode != 0:
            print_error(f"Failed to apply nginx ingress: {stderr}")
            return False
        print_success("  Nginx Ingress Controller manifest applied")

        # Wait for nginx ingress pods to be ready
        print_info("  Waiting for Nginx Ingress pods to be ready (may take 1-2 minutes)...")
        wait_cmd = "kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx --timeout=300s"
        returncode, _, stderr = run_command(wait_cmd, check=False)

        if returncode == 0:
            print_success("Nginx Ingress Controller is ready")
            return True

        print_warning("Nginx Ingress installed but not yet ready")
        print_info("Check status: kubectl get pods -n ingress-nginx")
        return True  # Return True as it's installed, just not ready yet

    def check_ingress_controller(self) -> bool:
        """Check if nginx ingress controller is installed"""
        print_info("Checking nginx ingress controller...")

        command = "kubectl get namespace ingress-nginx"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode != 0:
            print_warning("nginx ingress controller not found")
            print_info("Attempting to install nginx ingress controller...")
            if self.install_nginx_ingress():
                # Re-check after installation
                returncode, _, _ = run_command(command, check=False)
                if returncode == 0:
                    print_success("nginx ingress controller is now available")
                    return True
            print_error("Failed to install nginx ingress controller")
            self.warnings += 1
            return False

        # Check if pods are running
        command = "kubectl get pods -n ingress-nginx -o jsonpath='{.items[*].status.phase}'"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode == 0 and stdout:
            all_running = all(status == "Running" for status in stdout.split())
            if all_running:
                print_success("nginx ingress controller installed and running")
                return True
            else:
                print_warning("nginx ingress controller pods not all running")
                print_info("Check status: kubectl get pods -n ingress-nginx")
                self.warnings += 1
                return False

        print_success("nginx ingress controller installed")
        return True

    def run_all_checks(self) -> bool:
        """Run all prerequisite checks"""
        print(f"{Colors.BOLD}{Colors.HEADER}")
        print("=" * 70)
        print("  E-COMMERCE BACKEND - PREREQUISITES CHECK")
        print("=" * 70)
        print(f"{Colors.END}\n")

        checks = [
            ("CLI Tools", [
                ("kubectl", self.check_kubectl),
                ("AWS CLI", self.check_aws_cli),
                ("Docker", self.check_docker),
            ]),
            ("AWS Configuration", [
                ("AWS Credentials", self.check_aws_credentials),
                ("Secrets Manager", self.check_secrets_manager),
                ("IAM Role", self.check_iam_role),
                ("ECR Repository", self.check_ecr_repository),
            ]),
            ("Kubernetes Configuration", [
                ("Cluster Connection", self.check_cluster_connection),
                ("Namespace", self.check_namespace),
                ("Service Account", self.check_service_account),
                ("Ingress Controller", self.check_ingress_controller),
            ]),
        ]

        for section_name, section_checks in checks:
            print_section(section_name)

            for check_name, check_func in section_checks:
                try:
                    result = check_func()
                    if result:
                        self.checks_passed += 1
                    else:
                        self.checks_failed += 1
                except Exception as e:
                    print_error(f"Error checking {check_name}: {e}")
                    self.checks_failed += 1

        # Summary
        print(f"\n{Colors.BOLD}{Colors.CYAN}")
        print("=" * 70)
        print("  SUMMARY")
        print("=" * 70)
        print(f"{Colors.END}\n")

        print(f"{Colors.GREEN}✓ Checks passed: {self.checks_passed}{Colors.END}")
        print(f"{Colors.RED}✗ Checks failed: {self.checks_failed}{Colors.END}")
        print(f"{Colors.YELLOW}⚠ Warnings: {self.warnings}{Colors.END}")

        if self.checks_failed == 0 and self.warnings == 0:
            print(f"\n{Colors.BOLD}{Colors.GREEN}All prerequisites met! Ready to deploy.{Colors.END}")
            return True
        elif self.checks_failed == 0:
            print(f"\n{Colors.BOLD}{Colors.YELLOW}All critical prerequisites met, but there are warnings.{Colors.END}")
            print(f"{Colors.YELLOW}Review the warnings above before deploying.{Colors.END}")
            return True
        else:
            print(f"\n{Colors.BOLD}{Colors.RED}Some prerequisites are missing.{Colors.END}")
            print(f"{Colors.RED}Fix the errors above before deploying.{Colors.END}")
            return False


def main():
    """Main function"""
    checker = PrerequisiteChecker()
    success = checker.run_all_checks()

    if success:
        print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
        print("1. If IRSA is not set up, run:")
        print("   ./setup_irsa.py")
        print("\n2. Deploy the backend:")
        print("   ./deploy_backend.py")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Check interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
