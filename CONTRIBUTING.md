# Contributing to FinOps Lite

Thank you for your interest in contributing to FinOps Lite! We welcome contributions from the community.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature or bug fix
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/finops-lite.git
cd finops-lite

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Check code quality
black finops_lite/
flake8 finops_lite/
```

## Code Style

- Use Black for code formatting: `black finops_lite/`
- Follow PEP 8 guidelines
- Add type hints where appropriate
- Write descriptive commit messages

## Testing

- Add tests for new features
- Ensure all tests pass: `pytest`
- Maintain test coverage above 90%

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all CI checks pass
4. Update CHANGELOG.md if applicable
5. Request review from maintainers

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Provide clear reproduction steps for bugs
- Include environment details (Python version, OS, etc.)

## Questions?

Feel free to open an issue for questions or reach out to the maintainers.