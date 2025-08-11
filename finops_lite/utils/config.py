"""Configuration management for FinOps Lite."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


@dataclass
class AWSConfig:
    """AWS-specific configuration."""
    profile: Optional[str] = None
    region: Optional[str] = None
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    assume_role_arn: Optional[str] = None
    assume_role_session_name: Optional[str] = None


@dataclass
class OutputConfig:
    """Output formatting configuration."""
    format: str = "table"  # table, json, csv, yaml
    color: bool = True
    verbose: bool = False
    quiet: bool = False
    currency: str = "USD"
    decimal_places: int = 2


@dataclass 
class CostConfig:
    """Cost analysis configuration."""
    default_days: int = 30
    cost_threshold: float = 0.01  # Hide costs below this threshold
    group_by: List[str] = None
    dimensions: List[str] = None
    metrics: List[str] = None
    
    def __post_init__(self):
        if self.group_by is None:
            self.group_by = ["SERVICE"]
        if self.dimensions is None:
            self.dimensions = ["SERVICE", "LINKED_ACCOUNT", "REGION"]
        if self.metrics is None:
            self.metrics = ["BlendedCost", "UnblendedCost", "UsageQuantity"]


@dataclass
class TaggingConfig:
    """Tagging compliance configuration."""
    required_tags: List[str] = None
    cost_allocation_tags: List[str] = None
    ignore_resources: List[str] = None
    tag_enforcement: bool = True
    
    def __post_init__(self):
        if self.required_tags is None:
            self.required_tags = ["Environment", "Owner", "Project"]
        if self.cost_allocation_tags is None:
            self.cost_allocation_tags = ["Environment", "Owner", "Project", "CostCenter"]
        if self.ignore_resources is None:
            self.ignore_resources = []


@dataclass
class AlertConfig:
    """Alert and notification configuration."""
    cost_spike_threshold: float = 1000.0  # Dollar amount
    cost_spike_percentage: float = 0.20   # 20% increase
    anomaly_detection: bool = True
    notification_channels: List[str] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = []


class FinOpsConfig:
    """Main configuration class for FinOps Lite."""
    
    def __init__(
        self,
        config_file: Optional[Union[str, Path]] = None,
        aws_config: Optional[AWSConfig] = None,
        output_config: Optional[OutputConfig] = None,
        cost_config: Optional[CostConfig] = None,
        tagging_config: Optional[TaggingConfig] = None,
        alert_config: Optional[AlertConfig] = None,
    ):
        self.config_file = config_file
        self.aws = aws_config or AWSConfig()
        self.output = output_config or OutputConfig()
        self.cost = cost_config or CostConfig()
        self.tagging = tagging_config or TaggingConfig()
        self.alerts = alert_config or AlertConfig()
        
        # Load configuration from file if provided
        if config_file:
            self.load_from_file(config_file)
        
        # Override with environment variables
        self._load_from_environment()
    
    @classmethod
    def load_from_file(cls, config_path: Union[str, Path]) -> 'FinOpsConfig':
        """Load configuration from YAML file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        
        # Parse configuration sections
        aws_config = AWSConfig(**data.get('aws', {}))
        output_config = OutputConfig(**data.get('output', {}))
        cost_config = CostConfig(**data.get('cost', {}))
        tagging_config = TaggingConfig(**data.get('tagging', {}))
        alert_config = AlertConfig(**data.get('alerts', {}))
        
        return cls(
            config_file=config_path,
            aws_config=aws_config,
            output_config=output_config,
            cost_config=cost_config,
            tagging_config=tagging_config,
            alert_config=alert_config,
        )
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables."""
        # AWS configuration
        if os.getenv('AWS_PROFILE'):
            self.aws.profile = os.getenv('AWS_PROFILE')
        if os.getenv('AWS_DEFAULT_REGION'):
            self.aws.region = os.getenv('AWS_DEFAULT_REGION')
        if os.getenv('AWS_ACCESS_KEY_ID'):
            self.aws.access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        if os.getenv('AWS_SECRET_ACCESS_KEY'):
            self.aws.secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        if os.getenv('AWS_SESSION_TOKEN'):
            self.aws.session_token = os.getenv('AWS_SESSION_TOKEN')
        
        # FinOps specific environment variables
        if os.getenv('FINOPS_OUTPUT_FORMAT'):
            self.output.format = os.getenv('FINOPS_OUTPUT_FORMAT')
        if os.getenv('FINOPS_NO_COLOR'):
            self.output.color = False
        if os.getenv('FINOPS_VERBOSE'):
            self.output.verbose = True
        if os.getenv('FINOPS_QUIET'):
            self.output.quiet = True
        if os.getenv('FINOPS_CURRENCY'):
            self.output.currency = os.getenv('FINOPS_CURRENCY')
        
        # Cost configuration
        if os.getenv('FINOPS_DEFAULT_DAYS'):
            try:
                self.cost.default_days = int(os.getenv('FINOPS_DEFAULT_DAYS'))
            except ValueError:
                pass
        
        # Required tags from environment
        if os.getenv('FINOPS_REQUIRED_TAGS'):
            tags = os.getenv('FINOPS_REQUIRED_TAGS').split(',')
            self.tagging.required_tags = [tag.strip() for tag in tags]
    
    def get_boto3_session(self) -> boto3.Session:
        """Create and return a configured boto3 session."""
        session_kwargs = {}
        
        # Use profile if specified
        if self.aws.profile:
            session_kwargs['profile_name'] = self.aws.profile
        
        # Override with explicit credentials if provided
        if self.aws.access_key_id and self.aws.secret_access_key:
            session_kwargs.update({
                'aws_access_key_id': self.aws.access_key_id,
                'aws_secret_access_key': self.aws.secret_access_key,
            })
            if self.aws.session_token:
                session_kwargs['aws_session_token'] = self.aws.session_token
        
        # Set region
        if self.aws.region:
            session_kwargs['region_name'] = self.aws.region
        
        try:
            session = boto3.Session(**session_kwargs)
            
            # Test the session to ensure credentials work
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            # Assume role if specified
            if self.aws.assume_role_arn:
                sts_client = session.client('sts')
                assumed_role = sts_client.assume_role(
                    RoleArn=self.aws.assume_role_arn,
                    RoleSessionName=self.aws.assume_role_session_name or 'finops-lite-session'
                )
                
                # Create new session with assumed role credentials
                session = boto3.Session(
                    aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
                    aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
                    aws_session_token=assumed_role['Credentials']['SessionToken'],
                    region_name=self.aws.region or session.region_name
                )
            
            return session
            
        except (NoCredentialsError, PartialCredentialsError) as e:
            raise ValueError(f"AWS credentials not configured properly: {e}")
        except Exception as e:
            raise ValueError(f"Error creating AWS session: {e}")
    
    def validate_aws_permissions(self) -> Dict[str, bool]:
        """Validate that AWS credentials have required permissions."""
        session = self.get_boto3_session()
        permissions = {}
        
        # Test Cost Explorer permissions
        try:
            ce_client = session.client('ce')
            ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': '2024-01-01',
                    'End': '2024-01-02'
                },
                Granularity='DAILY',
                Metrics=['BlendedCost']
            )
            permissions['cost_explorer'] = True
        except Exception:
            permissions['cost_explorer'] = False
        
        # Test Resource Groups Tagging API permissions
        try:
            tagging_client = session.client('resourcegroupstaggingapi')
            tagging_client.get_resources(ResourcesPerPage=1)
            permissions['resource_tagging'] = True
        except Exception:
            permissions['resource_tagging'] = False
        
        # Test EC2 permissions (for rightsizing)
        try:
            ec2_client = session.client('ec2')
            ec2_client.describe_instances(MaxResults=5)
            permissions['ec2'] = True
        except Exception:
            permissions['ec2'] = False
        
        return permissions
    
    def save_to_file(self, config_path: Union[str, Path]) -> None:
        """Save current configuration to YAML file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert configuration to dictionary
        config_data = {
            'aws': {
                'profile': self.aws.profile,
                'region': self.aws.region,
                'assume_role_arn': self.aws.assume_role_arn,
                'assume_role_session_name': self.aws.assume_role_session_name,
                # Don't save sensitive credentials to file
            },
            'output': {
                'format': self.output.format,
                'color': self.output.color,
                'verbose': self.output.verbose,
                'quiet': self.output.quiet,
                'currency': self.output.currency,
                'decimal_places': self.output.decimal_places,
            },
            'cost': {
                'default_days': self.cost.default_days,
                'cost_threshold': self.cost.cost_threshold,
                'group_by': self.cost.group_by,
                'dimensions': self.cost.dimensions,
                'metrics': self.cost.metrics,
            },
            'tagging': {
                'required_tags': self.tagging.required_tags,
                'cost_allocation_tags': self.tagging.cost_allocation_tags,
                'ignore_resources': self.tagging.ignore_resources,
                'tag_enforcement': self.tagging.tag_enforcement,
            },
            'alerts': {
                'cost_spike_threshold': self.alerts.cost_spike_threshold,
                'cost_spike_percentage': self.alerts.cost_spike_percentage,
                'anomaly_detection': self.alerts.anomaly_detection,
                'notification_channels': self.alerts.notification_channels,
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"FinOpsConfig(aws_region={self.aws.region}, output_format={self.output.format})"


def get_default_config_paths() -> List[Path]:
    """Get list of default configuration file paths to check."""
    home = Path.home()
    cwd = Path.cwd()
    
    return [
        cwd / "finops.yaml",
        cwd / "finops.yml",
        cwd / ".finops.yaml",
        cwd / ".finops.yml",
        home / ".config" / "finops" / "config.yaml",
        home / ".config" / "finops" / "config.yml",
        home / ".finops.yaml",
        home / ".finops.yml",
    ]


def load_config(config_file: Optional[Union[str, Path]] = None) -> FinOpsConfig:
    """Load configuration from file or defaults."""
    if config_file:
        return FinOpsConfig.load_from_file(config_file)
    
    # Try default locations
    for config_path in get_default_config_paths():
        if config_path.exists():
            return FinOpsConfig.load_from_file(config_path)
    
    # No config file found, use defaults with environment variables
    return FinOpsConfig()