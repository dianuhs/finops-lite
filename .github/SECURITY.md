# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in FinOps Lite, please report it responsibly:

- **Do NOT** create a public GitHub issue
- Email security concerns directly to the maintainers
- Include detailed steps to reproduce the vulnerability
- Allow time for the issue to be addressed before public disclosure

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | ✅ Yes             |
| < 0.1   | ❌ No              |

## Security Considerations

### AWS Credentials
- FinOps Lite requires AWS credentials with **read-only access only**
- Never use credentials with write permissions
- Use IAM roles with minimal required permissions
- Consider using AWS profiles instead of environment variables

### Data Handling
- Cost data is cached locally in `~/.finops/cache/`
- Cache files contain cost information - secure your local environment
- No cost data is transmitted outside of AWS APIs
- All API calls are logged for debugging purposes only

### API Costs
- FinOps Lite makes AWS Cost Explorer API calls (~$0.01 each)
- Caching minimizes API usage and associated costs
- Monitor your AWS bill for unexpected Cost Explorer charges

## Best Practices

1. **Use read-only IAM policies**
2. **Enable AWS CloudTrail** to monitor API usage
3. **Regularly rotate AWS credentials**
4. **Keep FinOps Lite updated** to the latest version
5. **Review cache files** if sharing systems with others

## Contact

For security-related questions or to report vulnerabilities, please contact the maintainers through GitHub.
