"""
Test script to verify AWS Secrets Manager connection
Run this to ensure boto3 can retrieve your RDS credentials
"""
import os
import sys
from pathlib import Path

# Add the project to the path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables
from decouple import config
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Test the connection
def test_secrets_manager():
    """Test AWS Secrets Manager connection"""
    print("=" * 60)
    print("Testing AWS Secrets Manager Connection")
    print("=" * 60)

    # Display configuration
    secret_name = config('AWS_SECRET_NAME', default='ecommerce2')
    region = config('AWS_REGION', default='us-east-1')
    use_aws = config('USE_AWS_SECRETS', default='False')

    print(f"\nConfiguration:")
    print(f"  Secret Name: {secret_name}")
    print(f"  Region: {region}")
    print(f"  USE_AWS_SECRETS: {use_aws}")
    print()

    # Try to retrieve the secret
    try:
        from config.utils.aws_secrets import get_rds_credentials

        print("Attempting to retrieve credentials from AWS Secrets Manager...")
        print()

        db_config = get_rds_credentials()

        print("=" * 60)
        print("✅ SUCCESS! Retrieved database credentials")
        print("=" * 60)
        print(f"\nDatabase Configuration:")
        print(f"  Engine: {db_config['ENGINE']}")
        print(f"  Database: {db_config['NAME']}")
        print(f"  User: {db_config['USER']}")
        print(f"  Host: {db_config['HOST']}")
        print(f"  Port: {db_config['PORT']}")
        print(f"  Password: {'*' * len(db_config['PASSWORD'])} (hidden)")
        print()

        return True

    except Exception as e:
        print("=" * 60)
        print("❌ FAILED to retrieve credentials")
        print("=" * 60)
        print(f"\nError: {str(e)}")
        print()
        print("Common issues:")
        print("  1. AWS credentials not configured (run: aws configure)")
        print("  2. IAM permissions missing (need secretsmanager:GetSecretValue)")
        print("  3. Secret name doesn't exist in the specified region")
        print("  4. boto3 not installed (run: pip install boto3)")
        print()

        return False


if __name__ == '__main__':
    success = test_secrets_manager()
    sys.exit(0 if success else 1)
