# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, report them via:

- **Email**: security@teleagent-skills.dev
- **GitHub Security Advisory**: Use the [Security Advisories](https://github.com/yuzhaopeng-up/teleagent-skills/security/advisories) feature

You should receive a response within 48 hours. If the vulnerability is confirmed:

1. We will acknowledge your report and begin investigation
2. We will work on a fix and coordinate disclosure with you
3. We will release a patch and publicly credit your contribution (unless you prefer to remain anonymous)

## Security Principles

### Data Safety
- **Zero PII tolerance**: No real personally identifiable information in any file
- **Synthetic data only**: All examples use completely fabricated data
- **Desensitization by default**: Every skill's Phase 4 applies automatic desensitization

### Access Control
- **Read-only data access**: Skills operate on provided data; they do not directly access databases
- **Least privilege**: Each phase only has access to the data it needs from the previous phase's JSON output
- **No credential storage**: API keys and secrets are never stored in the repository

### Prompt Injection Defense
- All skills treat user input as untrusted
- Structured JSON contracts between phases limit injection surface
- Output sanitization in Phase 3 prevents leakage of internal reasoning

## Desensitization Checklist

Every contribution must pass this checklist before merge:

### Person Information
- [ ] No real person names (use `Person_A`, `Person_B`)
- [ ] No real email addresses (use `user@example.com`)
- [ ] No real phone numbers (use `138****1234`)
- [ ] No real ID numbers (use `XXXXXXXXXXXX1234`)

### Organization Information
- [ ] No real company names (use `Company_X`, `Org_Y`)
- [ ] No real internal department names (use `Dept_A`)
- [ ] No real project codenames that could identify the organization

### Technical Information
- [ ] No API keys, tokens, or secrets
- [ ] No internal IP addresses (use `10.x.x.x` ranges)
- [ ] No internal hostnames or domain names
- [ ] No database connection strings
- [ ] No file paths that reveal internal infrastructure

### Financial Information
- [ ] No real revenue figures (use rounded anonymized values)
- [ ] No real account numbers
- [ ] No real transaction IDs

### Verification Process
1. **Self-check**: Contributor runs the checklist before PR
2. **Automated scan**: CI pipeline runs regex-based secret detection on every PR
3. **Peer review**: At least one reviewer checks for desensitization
4. **Final gate**: Maintainer approval required before merge

## Automated Security Scanning

Every PR automatically triggers our security scan workflow (`.github/workflows/security-scan.yml`) which checks for:

- Hardcoded secrets (API keys, tokens, passwords)
- PII patterns (email addresses, phone numbers, ID numbers)
- Sensitive file inclusions (`.env`, credential files)
- Large files that might contain embedded data

If the scan fails, the PR cannot be merged until all findings are resolved.

## Responsible Disclosure

We follow responsible disclosure practices:

1. **Do not** publicly disclose vulnerabilities before a fix is available
2. **Do** give us reasonable time to respond and fix (typically 90 days)
3. **Do** coordinate with us on disclosure timing
4. **We will** credit security researchers in our advisories (unless anonymity is requested)

## Security Contact

For any security concerns:
- **Email**: security@teleagent-skills.dev
- **PGP Key**: Available on request
- **Response Time**: 48 hours for acknowledgment, 7 days for initial assessment
