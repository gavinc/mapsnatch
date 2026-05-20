# PyPI publishing (one-time operator setup)

Releases run on tag push `v*` via [.github/workflows/release.yml](https://github.com/gavinc/mapsnatch/blob/main/.github/workflows/release.yml).

## Trusted publishing (recommended)

1. Create/login at [pypi.org](https://pypi.org) — project name **`mapsnatch`** (first release claims the name).
2. PyPI → **Publishing** → **Add a new pending publisher**
   - PyPI project name: `mapsnatch`
   - Owner: `gavinc`
   - Repository: `mapsnatch`
   - Workflow: `release.yml`
   - Environment: `pypi`
3. GitHub → `gavinc/mapsnatch` → **Settings → Environments** → create **`pypi`** (no secrets required for OIDC).

## First release

```bash
git tag v0.1.0
git push origin v0.1.0
```

Watch **Actions → Release** and confirm `pip install mapsnatch` works.

## Fallback: API token

If OIDC is painful, add secret `PYPI_API_TOKEN` to environment `pypi` and the same workflow will use it (gh-action-pypi-publish supports both).
