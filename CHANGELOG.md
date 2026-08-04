# Changelog

## 0.2.0 — 2026-08-04

- Add a standard `finops-lite --version` installation smoke check.
- Add deterministic `finops ccac --demo` and real AWS `finops ccac` output conforming to `ccac/1.0.0`.
- Emit source identity/version, content hashes, evidence references, canonical metrics, and exact service/daily reconciliation.
- Fetch the complete service set for canonical output rather than a top-ten truncation.
- Reject missing, malformed, NaN, and infinite monetary values instead of coercing them to zero.
- Delay cache-directory creation so help, version, and credential-free demo paths work with an unavailable home directory.
- Correct repository metadata and accurately document AWS-only native API support.
- Retire the false “FOCUS 2026” claim; retain the old command only as a deprecated experimental compatibility path.
- Add CCAC, determinism, reconciliation, strict-numeric, and home-write tests.
- Expand the canonical illustrative fixture to 21 consecutive days with a deliberate final-day spike so Watchdog's default history window can run without weakening its evidence requirements.
- Emit daily-by-service metrics reconciled to both daily totals and period service totals.
- Reject missing Cost Explorer days instead of silently emitting observed zero spend.

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

### Added
- **FOCUS 1.0 column names** — `finops export focus` now outputs proper FOCUS 1.0 compliant column names: `BilledCost`, `ResourceId`, `ServiceName`, `ChargePeriodStart`, `ChargePeriodEnd`, `ChargeType`.
- **Azure Cost Management support** — `finops ingest focus --file billing.csv` auto-detects Azure billing CSV exports by column signature (`BillingCurrency`, `CostInBillingCurrency`, `SubscriptionId`) and normalizes to FOCUS 1.0 output.
- **GCP Billing export support** — same `ingest focus` command handles GCP billing CSV exports (detected via `usage_start_time` and `service.description` columns).
- **Multi-cloud provider auto-detection** — inspects CSV column names and dispatches to the correct provider parser without requiring a `--provider` flag.
- **Pipeline framing** — README rewritten to open with the Visibility → Variance → Tradeoffs system context and cross-links to all four pipeline tools.
- **GitHub Actions CI** — pytest runs on Python 3.10, 3.11, and 3.12 on every push.
- **examples/** — sample AWS billing CSV and expected output walkthrough.

### Planned
- Multi-account support for organizations
- Real-time cost alerts with Slack/email integration
- Budget tracking and forecasting
