# Contributing to TeleAgent Skills

Thank you for your interest in contributing! This guide covers everything you need to know.

## How to Contribute

1. **Fork** the repository
2. Create a **feature branch** from `main`: `git checkout -b feature/your-skill-name`
3. Make your changes following the guidelines below
4. Run the desensitization checklist (see below)
5. Submit a **Pull Request** with a clear description

### PR Checklist

- [ ] All example data is fully anonymized
- [ ] No real customer information, API keys, or secrets
- [ ] SKILL.md follows the standard structure
- [ ] YAML config files have sensible defaults
- [ ] JSON contracts between phases are well-defined
- [ ] Graceful degradation is documented
- [ ] README updated if adding a new skill

## Skill Structure Requirements

Every skill directory must follow this structure:

```
skills/your-skill-name/
├── SKILL.md              # Main skill definition (required)
├── config.yaml           # Parameterized rule config (required)
├── examples/             # Usage examples (recommended)
│   ├── basic.json        # Minimal usage example
│   └── advanced.json     # Complex usage example
├── contracts/            # Phase I/O contracts (recommended)
│   ├── phase1-input.json
│   ├── phase1-output.json
│   ├── phase2-input.json
│   ├── phase2-output.json
│   ├── phase3-input.json
│   ├── phase3-output.json
│   ├── phase4-input.json
│   └── phase4-output.json
└── tests/                # Test cases (recommended)
    └── test-cases.json
```

### SKILL.md Template

```markdown
# Skill Name

> One-line description

## Trigger
- Keywords: ...
- Scenarios: ...

## 4-Phase Orchestration

### Phase 1: Extract (Info-Extractor)
- Input: { ... }
- Output: { ... }

### Phase 2: Analyze (Data-Analyst)
- Input: { ... }
- Output: { ... }

### Phase 3: Generate (Report-Generator)
- Input: { ... }
- Output: { ... }

### Phase 4: Archive (Archive-Manager)
- Input: { ... }
- Output: { ... }

## Degradation Strategy
- If Phase X fails: ...

## Config Reference
See config.yaml for rule definitions.
```

## 4-Phase Pattern Guide

### Phase 1: Extract (Info-Extractor)
Parse raw input into structured JSON. This phase is stateless and deterministic.

**MUST:**
- Define explicit JSON schema for output
- Handle missing fields with defaults, not errors
- Validate input format before processing

**MUST NOT:**
- Perform business logic or scoring
- Access external APIs or databases
- Make assumptions about downstream processing

### Phase 2: Analyze (Data-Analyst)
Apply business rules, compute scores, validate, or aggregate data.

**MUST:**
- Read rules from config.yaml, never hard-code
- Produce deterministic output for identical input + config
- Document all computed fields with formulas

**MUST NOT:**
- Format output for display (that's Phase 3)
- Directly access databases (that's the data-executor component)
- Skip validation steps

### Phase 3: Generate (Report-Generator)
Format analysis results into human-readable or machine-consumable output.

**MUST:**
- Support at least 2 output formats (markdown + JSON)
- Include a 5-module template: Executive Summary, Data Tables, Analysis, Recommendations, Metadata
- Label degraded outputs clearly

**MUST NOT:**
- Perform new calculations (that's Phase 2)
- Include raw internal data structures
- Omit confidence scores or limitations

### Phase 4: Archive (Archive-Manager)
Desensitize, persist, and create audit trail.

**MUST:**
- Run desensitization on all PII before persisting
- Generate unique archive IDs
- Create audit log entries

**MUST NOT:**
- Persist un-anonymized data
- Skip audit logging
- Overwrite existing archives (append only)

## Desensitization Checklist

Before submitting ANY PR, verify:

- [ ] **Names**: All person names replaced with `Person_A`, `Person_B`, etc.
- [ ] **Companies**: All company names replaced with `Company_X`, `Org_Y`, etc.
- [ ] **IDs**: All phone numbers, ID numbers, account numbers replaced with masked values (`138****1234`)
- [ ] **Addresses**: Specific addresses replaced with generic ones (`City_A, District_B`)
- [ ] **Financials**: Real revenue/amount replaced with rounded anonymized values (`5M`, `100K`)
- [ ] **API Keys**: No API keys, tokens, or secrets anywhere in the repo
- [ ] **Emails**: All email addresses replaced with `user@example.com` pattern
- [ ] **IPs**: All internal IP addresses replaced with `10.x.x.x` or `192.168.x.x` patterns
- [ ] **Timestamps**: Real timestamps can be kept if they don't reveal identifiable patterns

### Non-Negotiable Rules

1. **Zero tolerance for real PII** — If found, the PR will be rejected immediately
2. **No secrets in code** — Use environment variables or config files excluded from git
3. **Examples must be synthetic** — Even "obviously fake" data must not resemble real entities

## Code of Conduct

### Our Pledge

We pledge to make participation in this project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Trolling, insulting, or derogatory comments
- Public or private harassment
- Publishing others' private information without permission
- Conduct which could reasonably be considered inappropriate

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team. All complaints will be reviewed and investigated and will result in a response that is deemed necessary and appropriate. The project team is obligated to maintain confidentiality with regard to the reporter.

Project maintainers who do not follow or enforce the Code of Conduct may face temporary or permanent repercussions.

### Attribution

This Code of Conduct is adapted from the [Contributor Covenant](https://www.contributor-covenant.org/), version 2.1.

## Questions?

Open an issue with the `question` label, and we'll get back to you.
