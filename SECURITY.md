# Security policy

## Supported versions

Only the latest release gets security fixes.

## Reporting a vulnerability

Please report vulnerabilities privately through [GitHub private vulnerability reporting](https://github.com/azharudh33n/ai-organization/security/advisories/new). Don't open a public issue. You should get a reply within 7 days.

Examples of what counts:

- instructions in the skill that could make an agent exfiltrate data, run untrusted code or skip the user's approval
- weaknesses in the CI or release workflows, such as token scope, injection or unpinned dependencies
- a release artifact that fails `gh attestation verify`

## Verifying a release

```bash
gh attestation verify ai-organization-skill.zip -R azharudh33n/ai-organization
```
