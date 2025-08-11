"""
FinOps Lite - AWS FinOps CLI for cost visibility, optimization, and governance.

A professional-grade command-line tool that brings AWS cost management 
directly to your terminal.
"""

__version__ = "0.1.0"
__author__ = "Diana"
__email__ = "your.email@example.com"

from .utils.config import FinOpsConfig, load_config

__all__ = ["FinOpsConfig", "load_config", "__version__"]