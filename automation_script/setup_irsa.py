#!/usr/bin/env python3
"""
IRSA (IAM Roles for Service Accounts) Setup Script for EKS Backend
Configures IAM roles, policies, and Kubernetes service accounts for AWS Secrets Manager access.
"""

import subprocess
import sys
import json
import time
from typing import Tuple, Optional, Dict


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


def print_step(message: str):
    """Print a formatted step message"""
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


class IRSASetup:
    """IRSA setup manager"""

    def __init__(self, config: Dict[str, str]):
        self.cluster_name = config['cluster_name']
        self.region = config['region']
        self.account_id = config['account_id']
        self.namespace = config['namespace']
        self.service_account_name = config['service_account_name']
        self.policy_name = config['policy_name']
        self.role_name = config['role_name']
        self.secret_name = config['secret_name']

    def display_configuration(self):
        """Display configuration"""
        print_info("Configuration:")
        print(f"  Cluster:         {self.cluster_name}")
        print(f"  Region:          {self.region}")
        print(f"  Account ID:      {self.account_id}")
        print(f"  Namespace:       {self.namespace}")
        print(f"  Service Account: {self.service_account_name}")
        print(f"  Role Name:       {self.role_name}")
        print(f"  Policy Name:     {self.policy_name}")
        print(f"  Secret Name:     {self.secret_name}")
        print()

    def get_oidc_provider(self) -> Tuple[str, str]:
        """Get OIDC provider URL and ARN for the cluster"""
        print_step("Getting OIDC Provider")

        # Get OIDC issuer URL
        command = f"aws eks describe-cluster --name {self.cluster_name} --region {self.region} --query 'cluster.identity.oidc.issuer' --output text"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode != 0:
            print_error(f"Failed to get OIDC provider: {stderr}")
            sys.exit(1)

        oidc_url = stdout.strip().replace('https://', '')
        print_info(f"OIDC Provider URL: {oidc_url}")

        # Get OIDC provider ARN
        oidc_id = oidc_url.split('/')[-1]
        command = f"aws iam list-open-id-connect-providers --query \"OpenIDConnectProviderList[?ends_with(Arn, '{oidc_id}')].Arn\" --output text"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode != 0 or not stdout.strip():
            print_error("OIDC provider not found for cluster")
            print_error(f"Create it with: eksctl utils associate-iam-oidc-provider --cluster={self.cluster_name} --region={self.region} --approve")
            sys.exit(1)

        oidc_arn = stdout.strip()
        print_success(f"OIDC Provider ARN: {oidc_arn}")

        return oidc_url, oidc_arn

    def create_iam_policy(self) -> str:
        """Create or update IAM policy with Secrets Manager and KMS permissions"""
        print_step("Creating IAM Policy")

        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret"
                    ],
                    "Resource": f"arn:aws:secretsmanager:{self.region}:{self.account_id}:secret:{self.secret_name}-*"
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

        # Write policy to temp file
        policy_file = "/tmp/iam_policy.json"
        with open(policy_file, 'w') as f:
            json.dump(policy_document, f, indent=2)

        policy_arn = f"arn:aws:iam::{self.account_id}:policy/{self.policy_name}"

        # Check if policy exists
        command = f"aws iam get-policy --policy-arn {policy_arn}"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode == 0:
            print_success(f"Policy already exists: {policy_arn}")

            # Update policy with new version
            print_info("Updating policy with new version...")
            command = f"aws iam create-policy-version --policy-arn {policy_arn} --policy-document file://{policy_file} --set-as-default"
            returncode, stdout, stderr = run_command(command, check=False)

            if returncode == 0:
                print_success("Updated policy with new version")
            else:
                print_warning(f"Could not update policy version: {stderr}")
                print_info("This may be normal if the policy is unchanged or version limit reached")
        else:
            # Create new policy
            command = f"aws iam create-policy --policy-name {self.policy_name} --policy-document file://{policy_file} --description 'Policy for EKS backend to access Secrets Manager and KMS'"
            returncode, stdout, stderr = run_command(command, check=False)

            if returncode == 0:
                print_success(f"Created policy: {policy_arn}")
            else:
                print_error(f"Failed to create policy: {stderr}")
                sys.exit(1)

        return policy_arn

    def create_iam_role(self, oidc_url: str, oidc_arn: str, policy_arn: str) -> str:
        """Create or update IAM role with trust relationship"""
        print_step("Creating IAM Role")

        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": oidc_arn
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Condition": {
                        "StringEquals": {
                            f"{oidc_url}:sub": f"system:serviceaccount:{self.namespace}:{self.service_account_name}",
                            f"{oidc_url}:aud": "sts.amazonaws.com"
                        }
                    }
                }
            ]
        }

        # Write trust policy to temp file
        trust_file = "/tmp/trust_policy.json"
        with open(trust_file, 'w') as f:
            json.dump(trust_policy, f, indent=2)

        role_arn = f"arn:aws:iam::{self.account_id}:role/{self.role_name}"

        # Check if role exists
        command = f"aws iam get-role --role-name {self.role_name}"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode == 0:
            print_success(f"Role already exists: {self.role_name}")

            # Update trust policy
            print_info("Updating trust policy...")
            command = f"aws iam update-assume-role-policy --role-name {self.role_name} --policy-document file://{trust_file}"
            returncode, stdout, stderr = run_command(command, check=False)

            if returncode == 0:
                print_success("Updated trust policy")
            else:
                print_error(f"Failed to update trust policy: {stderr}")
        else:
            # Create new role
            command = f"aws iam create-role --role-name {self.role_name} --assume-role-policy-document file://{trust_file} --description 'IAM role for EKS backend service to access AWS Secrets Manager'"
            returncode, stdout, stderr = run_command(command, check=False)

            if returncode == 0:
                print_success(f"Created role: {self.role_name}")
            else:
                print_error(f"Failed to create role: {stderr}")
                sys.exit(1)

        # Attach policy to role
        print_info("Attaching policy to role...")
        command = f"aws iam attach-role-policy --role-name {self.role_name} --policy-arn {policy_arn}"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode == 0:
            print_success("Policy attached to role")
        else:
            # Check if already attached
            if "already attached" in stderr.lower() or returncode == 0:
                print_success("Policy already attached to role")
            else:
                print_warning(f"Could not attach policy: {stderr}")

        return role_arn

    def create_kubernetes_service_account(self, role_arn: str):
        """Create Kubernetes service account with IAM role annotation"""
        print_step("Creating Kubernetes Service Account")

        # Check if namespace exists
        command = f"kubectl get namespace {self.namespace}"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode != 0:
            print_info(f"Creating namespace: {self.namespace}")
            command = f"kubectl create namespace {self.namespace}"
            returncode, stdout, stderr = run_command(command, check=False)
            if returncode == 0:
                print_success(f"Created namespace: {self.namespace}")
            else:
                print_error(f"Failed to create namespace: {stderr}")
                sys.exit(1)

        # Create service account YAML
        sa_yaml = f"""apiVersion: v1
kind: ServiceAccount
metadata:
  name: {self.service_account_name}
  namespace: {self.namespace}
  annotations:
    eks.amazonaws.com/role-arn: {role_arn}
"""

        sa_file = "/tmp/service_account.yaml"
        with open(sa_file, 'w') as f:
            f.write(sa_yaml)

        # Apply service account
        command = f"kubectl apply -f {sa_file}"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode == 0:
            print_success("Service account created/updated")
            print(f"  {stdout.strip()}")
        else:
            print_error(f"Failed to create service account: {stderr}")
            sys.exit(1)

        # Verify service account
        print_info("Verifying service account...")
        time.sleep(2)
        command = f"kubectl describe sa {self.service_account_name} -n {self.namespace}"
        returncode, stdout, stderr = run_command(command, check=False)

        if returncode == 0:
            # Print relevant lines
            for line in stdout.split('\n'):
                if 'role-arn' in line.lower() or 'name:' in line.lower():
                    print(f"  {line}")

    def run(self):
        """Execute the full IRSA setup"""
        print(f"{Colors.BOLD}{Colors.HEADER}")
        print("=" * 70)
        print("  IRSA SETUP FOR EKS BACKEND")
        print("=" * 70)
        print(f"{Colors.END}\n")

        self.display_configuration()

        # Get OIDC provider
        oidc_url, oidc_arn = self.get_oidc_provider()

        # Create IAM policy
        policy_arn = self.create_iam_policy()

        # Create IAM role
        role_arn = self.create_iam_role(oidc_url, oidc_arn, policy_arn)

        # Create Kubernetes service account
        self.create_kubernetes_service_account(role_arn)

        # Summary
        print(f"\n{Colors.BOLD}{Colors.GREEN}")
        print("=" * 70)
        print("  ✓ IRSA SETUP COMPLETE!")
        print("=" * 70)
        print(f"{Colors.END}\n")

        print(f"{Colors.BOLD}Details:{Colors.END}")
        print(f"  Service Account: {self.service_account_name}")
        print(f"  Namespace:       {self.namespace}")
        print(f"  IAM Role:        {self.role_name}")
        print(f"  IAM Role ARN:    {role_arn}")
        print(f"  IAM Policy:      {self.policy_name}")
        print(f"  Secret Name:     {self.secret_name}")

        print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
        print("1. Update your deployment to use the service account:")
        print(f"   spec.serviceAccountName: {self.service_account_name}")
        print("\n2. Verify the pod can access secrets:")
        print(f"   POD_NAME=$(kubectl get pods -n {self.namespace} -l app=ecommerce-backend -o jsonpath='{{.items[0].metadata.name}}')")
        print(f"   kubectl exec -it $POD_NAME -n {self.namespace} -- aws secretsmanager get-secret-value --secret-id {self.secret_name} --region {self.region}")

        print(f"\n{Colors.YELLOW}Note: If you get KMS access denied, update the KMS key policy to allow the role:{Colors.END}")
        print(f"   Role ARN: {role_arn}")


def main():
    """Main function"""

    # Configuration - These match the backend setup
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

    # Check if AWS CLI is available
    returncode, stdout, stderr = run_command("aws --version", check=False)
    if returncode != 0:
        print_error("AWS CLI is not installed or not in PATH")
        print_info("Install from: https://aws.amazon.com/cli/")
        sys.exit(1)

    # Check if kubectl is available
    returncode, stdout, stderr = run_command("kubectl version --client", check=False)
    if returncode != 0:
        print_error("kubectl is not installed or not in PATH")
        print_info("Install from: https://kubernetes.io/docs/tasks/tools/")
        sys.exit(1)

    print_success("Prerequisites check passed")

    # Run IRSA setup
    irsa = IRSASetup(config)
    irsa.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Setup interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
