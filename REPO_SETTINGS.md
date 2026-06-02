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
| **Branch protection** | Settings → Branches → `main` | Require PR, require aggregate **`ci`** — **only on public repos or GitHub Pro private repos** (see below) |
| **Secret scanning** | Settings → Code security | **Enabled** (May 2026) |
| **Secret push protection** | Settings → Code security | **Enabled** — blocks pushes with known secret patterns |
| **CodeQL** | Settings → Code security → Code scanning | **Enabled** — default setup, Python + Actions, weekly |
| **Environment `pypi`** | Settings → Environments | Create for trusted publishing (see [PYPI_SETUP.md](./PYPI_SETUP.md)) |
| **Sponsorships** | Settings → General → Features | **Enable** + valid [.github/FUNDING.yml](./.github/FUNDING.yml). Use Ko-fi **username** (`gavin_c`), not the page ID in the URL (`D5G31ZW8MC`). Verify with `gh api graphql` → `repository.fundingLinks` must be non-empty. No leading spaces or `#` comments in the committed file. |

## Security stack (current)

| Layer | What it catches |
|-------|------------------|
| **gitleaks** (`secret-scan` in `ci`) | Committed tokens in git history / PR diffs |
| **GitHub secret push protection** | Known-pattern secrets at `git push` time |
| **GitHub secret scanning** | Secrets already on default branch; partner alerts |
| **CodeQL** | Python/Actions code vulnerabilities (SAST) |
| **pip-audit** (`security-audit` in `ci`) | CVEs in runtime dependencies |

CodeQL is **not** wired into the required **`ci`** branch check unless you add CodeQL check names under branch protection.

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

## Visibility vs branch protection

On a **free** account, **private** repos cannot use branch protection (API 403). **Public** repos can — protection is applied via the CLI block above (`required_status_checks` → **`ci`**).

If the repo is flipped private again, protection rules are removed by GitHub; re-apply after returning to public (or use GitHub Pro for private protection).
