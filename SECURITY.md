# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| latest `main` | yes |
| older tags | best effort |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

Report privately to **security@mapsnatch.com** (or **support@mapsnatch.com** if you cannot reach security).

Include:

- Description of the issue and impact
- Steps to reproduce (if applicable)
- Your suggested fix (optional)

We aim to acknowledge reports within **3 business days** and will keep you updated on remediation. We prefer coordinated disclosure and will credit reporters in the release notes when you want that.

## What belongs here

- Bugs in this CLI that could leak tokens, write outside the output directory, or execute untrusted code
- Dependency vulnerabilities with a plausible exploit path in MapSnatch

## Out of scope

- Issues with MindMeister's API or account security (report to Meister Labs)
- The hosted web app at [mapsnatch.com](https://mapsnatch.com) (separate private deployment; still report via the same email and we will route it)

## Safe handling of API tokens

- Never commit tokens or paste them into public issues
- Use `.env` locally (gitignored) or `MINDMEISTER_API_TOKEN` in your shell
- Revoke and rotate tokens at [MindMeister API settings](https://www.mindmeister.com/api/settings) if you suspect exposure
