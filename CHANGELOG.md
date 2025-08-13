# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-12

### Added
- Initial release of FinOps Lite CLI
- Cost overview with month-to-date totals and service breakdown
- Beautiful terminal output with rich tables and progress indicators
- Intelligent caching system to minimize AWS API costs
- Cache management commands (`finops cache stats`, `finops cache clear`)
- Performance tracking with detailed metrics
- Multiple output formats (table, JSON, CSV, YAML, executive)
- Enhanced error handling with actionable AWS guidance
- Support for AWS Cost Explorer with automatic fallback handling
- Tag compliance reporting (demo mode)
- EC2 rightsizing recommendations (demo mode)
- Professional packaging with `finops` command entry point

### Enhanced Error Handling
- Beautiful error panels with specific guidance for AWS issues
- Cost Explorer not enabled detection and setup instructions
- AWS credentials missing with multiple resolution options
- API rate limiting with retry logic and exponential backoff
- Network timeout handling with automatic retries
- Permission error detection with required IAM policy suggestions

### Performance Features
- Intelligent API response caching with configurable TTL
- Cache hit/miss tracking with cost savings calculation
- Performance metrics and timing for all operations
- Concurrent API calls where possible
- Progress indicators for long-running operations
- Cache statistics and management commands

### CLI Features
- Global options for output format, caching, and performance tracking
- Dry-run mode for testing without AWS API calls
- Verbose mode with detailed optimization recommendations
- Force refresh option to bypass cache
- Export functionality for reports
- Professional help system with examples

### Development
- Comprehensive test suite with 37 test cases
- GitHub Actions CI/CD pipeline with automated testing
- Code quality checks (Black, Flake8, isort)
- Security scanning with Bandit and Trivy
- Professional packaging with setup.py and MANIFEST.in
- Development dependencies and tooling setup

## [Unreleased]

### Planned
- Real AWS Cost Explorer integration
- Multi-account support for organizations
- Real-time cost alerts with Slack/email integration
- Budget tracking and forecasting
- Custom dashboards and reporting
- API integration for programmatic access
- Interactive tag fixing functionality
- Advanced rightsizing analysis with historical data