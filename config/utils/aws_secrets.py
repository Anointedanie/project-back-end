"""
AWS Secrets Manager utility for retrieving RDS credentials
"""
import json
import boto3
from botocore.exceptions import ClientError
import logging
from decouple import config as env_config

logger = logging.getLogger(__name__)


def get_secret(secret_name=None, region_name=None):
    """
    Retrieve secret from AWS Secrets Manager
    
    Args:
        secret_name: Name or ARN of the secret
        region_name: AWS region where secret is stored
        
    Returns:
        dict: Parsed secret values
    """
    
    # Get configuration from environment
    if secret_name is None:
        secret_name = env_config(
            'AWS_SECRET_NAME',
            default='ecommerce2'
        )
    
    if region_name is None:
        region_name = env_config('AWS_REGION', default='us-east-1')
    
    logger.info(f"Retrieving secret from AWS Secrets Manager")
    logger.info(f"  Region: {region_name}")
    logger.info(f"  Secret: {secret_name[:50]}...")
    
    # Create a Secrets Manager client
    try:
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        
        # Parse the secret string
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        
        logger.info(f"✅ Successfully retrieved secret")
        logger.info(f"  Available keys: {list(secret_dict.keys())}")
        return secret_dict
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        logger.error(f"❌ AWS Secrets Manager error: {error_code}")
        logger.error(f"  Message: {error_message}")
        
        if error_code == 'AccessDeniedException':
            logger.error("💡 Troubleshooting:")
            logger.error("  1. Run: aws sts get-caller-identity")
            logger.error("  2. Verify your IAM user/role has access to Secrets Manager")
            logger.error("  3. Check IAM policy is attached to your user")
            logger.error("  4. Policy must allow secretsmanager:GetSecretValue")
        elif error_code == 'ResourceNotFoundException':
            logger.error(f"💡 Secret not found: {secret_name}")
        
        raise
            
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        raise


def get_rds_credentials():
    """
    Get RDS credentials in Django-compatible format
    
    Returns:
        dict: Database configuration dict
    """
    try:
        secret = get_secret()
        
        # RDS auto-generated secrets use these key names
        # Map them to Django database settings
        db_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': secret.get('dbname', secret.get('database', 'postgres')),
            'USER': secret.get('username', secret.get('user')),
            'PASSWORD': secret.get('password'),
            'HOST': secret.get('host'),
            'PORT': int(secret.get('port', 5432)),
            'OPTIONS': {
                'connect_timeout': 10,
            }
        }
        
        # Validate required fields
        if not all([db_config['USER'], db_config['PASSWORD'], db_config['HOST']]):
            raise ValueError("Secret missing required database credentials")
        
        logger.info(f"✅ Database configuration ready")
        logger.info(f"  Database: {db_config['NAME']}")
        logger.info(f"  User: {db_config['USER']}")
        logger.info(f"  Host: {db_config['HOST']}")
        logger.info(f"  Port: {db_config['PORT']}")
        
        return db_config
        
    except Exception as e:
        logger.error(f"❌ Failed to get RDS credentials: {str(e)}")
        raise