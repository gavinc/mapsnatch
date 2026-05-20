# GitHub repository settings (Tier H)

Operator checklist for `gavinc/mapsnatch`. Some steps require repo admin on GitHub.

## Automated (via `gh` where possible)

Run from a machine with admin on the repo:

```bash
# Merge hygene
gh api repos/gavinc/mapsnatch -X PATCH \
  -f delete_branch_on_merge=true \
  -f allow_squash_merge=true \
  -f allow_merge_commit=false \
  -f allow_rebase_merge=false

# Dependabot alerts + automated security fix PRs
gh api repos/gavinc/mapsnatch/vulnerability-alerts -X PUT
gh api repos/gavinc/mapsnatch/automated-security-fixes -X PUT
```

## Click in GitHub UI

| Setting | Path | Value |
|---------|------|-------|
| **GitHub Pages** | Settings → Pages | Source: **GitHub Actions** |
| **Private vulnerability reporting** | Settings → Security → Private vulnerability reporting | **Enable** |
| **Social preview** | Settings → General → Social preview | Upload `.github/social-preview.png` (1280×640) |
| **Branch protection** | Settings → Branches → `main` | Require PR, require aggregate **`ci`** (lint + `secret-scan` + `security-audit`) |
| **Secret push protection** | Settings → Code security | Enable if available on plan (complements gitleaks in CI) |
| **Environment `pypi`** | Settings → Environments | Create for trusted publishing (see [PYPI_SETUP.md](./PYPI_SETUP.md)) |

## Branch protection (CLI)

```bash
gh api repos/gavinc/mapsnatch/branches/main/protection -X PUT \
  -f required_status_checks[strict]=true \
  -f required_status_checks[contexts][]=ci \
  -f enforce_admins=true \
  -f required_pull_request_reviews[required_approving_review_count]=0 \
  -f restrictions=null
```

Adjust `contexts` if the CI job name differs after the first workflow run.
