"""
AWS client utilities and session management.
Handles AWS authentication, retries, and error handling.
"""

import boto3
import botocore
from botocore.config import Config
from botocore.exceptions import (
    ClientError, 
    NoCredentialsError, 
    PartialCredentialsError,
    BotoCoreError
)
from typing import Dict, Any, Optional
import logging
import time
from functools import wraps

from .config import FinOpsConfig

logger = logging.getLogger(__name__)


class AWSClientError(Exception):
    """Custom exception for AWS client errors."""
    pass


class AWSClientManager:
    """Manages AWS clients with proper configuration and error handling."""
    
    def __init__(self, config: FinOpsConfig):
        self.config = config
        self.session = None
        self._clients = {}
        
        # Configure boto3 with retries and timeouts
        self.boto_config = Config(
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            read_timeout=60,
            connect_timeout=30,
            max_pool_connections=10
        )
        
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize boto3 session with configuration."""
        try:
            self.session = self.config.get_boto3_session()
            logger.info("AWS session initialized successfully")
            
            # Validate session by getting caller identity
            sts = self.get_client('sts')
            identity = sts.get_caller_identity()
            logger.info(f"Authenticated as: {identity.get('Arn', 'Unknown')}")
            
        except (NoCredentialsError, PartialCredentialsError) as e:
            raise AWSClientError(f"AWS credentials not configured: {e}")
        except Exception as e:
            raise AWSClientError(f"Failed to initialize AWS session: {e}")
    
    def get_client(self, service_name: str, region: Optional[str] = None) -> boto3.client:
        """
        Get or create an AWS service client.
        
        Args:
            service_name: AWS service name (e.g., 'ce', 'ec2', 'rds')
            region: AWS region (optional, uses session default)
            
        Returns:
            Configured boto3 client
        """
        client_key = f"{service_name}:{region or 'default'}"
        
        if client_key not in self._clients:
            try:
                kwargs = {'config': self.boto_config}
                if region:
                    kwargs['region_name'] = region
                
                self._clients[client_key] = self.session.client(service_name, **kwargs)
                logger.debug(f"Created {service_name} client for region {region or 'default'}")
                
            except Exception as e:
                raise AWSClientError(f"Failed to create {service_name} client: {e}")
        
        return self._clients[client_key]
    
    def get_resource(self, service_name: str, region: Optional[str] = None):
        """
        Get or create an AWS service resource.
        
        Args:
            service_name: AWS service name (e.g., 'ec2', 's3')
            region: AWS region (optional, uses session default)
            
        Returns:
            Configured boto3 resource
        """
        try:
            kwargs = {'config': self.boto_config}
            if region:
                kwargs['region_name'] = region
            
            return self.session.resource(service_name, **kwargs)
            
        except Exception as e:
            raise AWSClientError(f"Failed to create {service_name} resource: {e}")
    
    def validate_permissions(self, required_services: list) -> Dict[str, bool]:
        """
        Validate that the current credentials have access to required services.
        
        Args:
            required_services: List of AWS services to validate
            
        Returns:
            Dictionary mapping service names to permission status
        """
        permissions = {}
        
        for service in required_services:
            try:
                permissions[service] = self._test_service_access(service)
            except Exception as e:
                logger.warning(f"Could not test {service} permissions: {e}")
                permissions[service] = False
        
        return permissions
    
    def _test_service_access(self, service: str) -> bool:
        """Test access to a specific AWS service."""
        test_operations = {
            'ce': lambda client: client.get_cost_and_usage(
                TimePeriod={'Start': '2024-01-01', 'End': '2024-01-02'},
                Granularity='DAILY',
                Metrics=['BlendedCost']
            ),
            'ec2': lambda client: client.describe_instances(MaxResults=5),
            'rds': lambda client: client.describe_db_instances(MaxRecords=1),
            'resourcegroupstaggingapi': lambda client: client.get_resources(ResourcesPerPage=1),
            'support': lambda client: client.describe_services(),
            'organizations': lambda client: client.describe_organization(),
        }
        
        if service not in test_operations:
            logger.warning(f"No test operation defined for service: {service}")
            return False
        
        try:
            client = self.get_client(service)
            test_operations[service](client)
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            # Some errors indicate permissions issues, others might be expected
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                return False
            elif error_code in ['InvalidParameterValue', 'ValidationException']:
                # These suggest we have permission but sent invalid parameters
                return True
            else:
                logger.warning(f"Unexpected error testing {service}: {error_code}")
                return False
                
        except Exception as e:
            logger.warning(f"Error testing {service} access: {e}")
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get AWS account information."""
        try:
            sts = self.get_client('sts')
            identity = sts.get_caller_identity()
            
            return {
                'account_id': identity.get('Account'),
                'user_arn': identity.get('Arn'),
                'user_id': identity.get('UserId'),
                'region': self.session.region_name
            }
            
        except Exception as e:
            raise AWSClientError(f"Failed to get account info: {e}")
    
    def list_available_regions(self, service: str) -> list:
        """List available regions for a service."""
        try:
            session = boto3.Session()
            return session.get_available_regions(service)
        except Exception as e:
            logger.warning(f"Could not list regions for {service}: {e}")
            return []


def retry_on_throttle(max_retries: int = 3, backoff_factor: float = 2.0):
    """
    Decorator to retry operations when AWS throttling occurs.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    
                    # Retry on throttling errors
                    if error_code in ['Throttling', 'ThrottlingException', 'RequestLimitExceeded']:
                        if attempt < max_retries:
                            delay = backoff_factor ** attempt
                            logger.warning(f"Throttled, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                            time.sleep(delay)
                            last_exception = e
                            continue
                    
                    # Don't retry on other errors
                    raise
                    
                except BotoCoreError as e:
                    # Don't retry on boto core errors
                    raise AWSClientError(f"AWS operation failed: {e}")
            
            # If we get here, all retries were exhausted
            raise AWSClientError(f"Operation failed after {max_retries} retries: {last_exception}")
        
        return wrapper
    return decorator


def handle_aws_errors(func):
    """
    Decorator to handle common AWS errors and convert them to user-friendly messages.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_message = e.response.get('Error', {}).get('Message', '')
            
            # Map common error codes to user-friendly messages
            error_mappings = {
                'AccessDenied': 'Insufficient permissions for this operation',
                'UnauthorizedOperation': 'Not authorized to perform this operation',
                'InvalidParameterValue': f'Invalid parameter: {error_message}',
                'ValidationException': f'Validation error: {error_message}',
                'Throttling': 'AWS API rate limit exceeded, please try again later',
                'ServiceUnavailable': 'AWS service temporarily unavailable',
                'InternalError': 'AWS internal error, please try again',
            }
            
            user_message = error_mappings.get(error_code, f"AWS error ({error_code}): {error_message}")
            raise AWSClientError(user_message)
            
        except (NoCredentialsError, PartialCredentialsError):
            raise AWSClientError("AWS credentials not configured properly")
            
        except BotoCoreError as e:
            raise AWSClientError(f"AWS operation failed: {e}")
            
        except Exception as e:
            raise AWSClientError(f"Unexpected error: {e}")
    
    return wrapper