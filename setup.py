"""
Setup script for FinOps Lite.
Provides backward compatibility for systems that don't support pyproject.toml.
"""

from setuptools import setup

# For systems that don't support pyproject.toml
if __name__ == "__main__":
    setup()
