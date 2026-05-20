# PyPI publishing (one-time operator setup)

Releases run on tag push `v*` via [.github/workflows/release.yml](.github/workflows/release.yml).

## You do not "create a project" on PyPI first

PyPI no longer has a separate "register project" step. The project **`mapsnatch`** is created automatically on the **first successful upload** of a wheel/sdist (name must still be available on PyPI).

Check availability: https://pypi.org/project/mapsnatch/ — 404 means the name is free.

## Option A — API token (fastest if you already have a token)

1. **PyPI account** — log in at [pypi.org](https://pypi.org).
2. **Create an API token** — Account settings → API tokens → scope **Entire account** (or project-scoped after first publish).
   - Token looks like `pypi-AgEIcHlwaS5vcmcC...`
3. **GitHub environment** — repo `gavinc/mapsnatch` → Settings → Environments → **`pypi`**
   - Add secret **`PYPI_API_TOKEN`** = your token (never commit it).
   - Operator copy may live in `~/coding/server-setup/.env` as `PYPI_API_TOKEN` — load into GitHub only, not the repo.
4. **First release** (from a clean `main`):

```bash
git tag v0.1.0
git push origin v0.1.0
```

5. Watch **Actions → Release**. When green:

```bash
pip install mapsnatch
mapsnatch --help
```

6. Update README "Install" section to lead with `pip install mapsnatch`.

## Option B — Trusted publishing (OIDC, no long-lived token)

Use this instead of Option A if you prefer no stored PyPI password on GitHub.

1. PyPI → **Publishing** → **Add a new pending publisher**
   - PyPI project name: `mapsnatch` (reserved on first publish, not before)
   - Owner: `gavinc`
   - Repository: `mapsnatch`
   - Workflow: `release.yml`
   - Environment: `pypi`
2. GitHub → same repo → Environment **`pypi`** exists (no `PYPI_API_TOKEN` secret required).
3. Tag push as in Option A step 4.

Do **not** configure both OIDC and a conflicting token unless you know which `gh-action-pypi-publish` will prefer; token in environment `pypi` is enough for Option A.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| "Project does not exist" in PyPI UI | Normal before first upload — publish once via workflow or `twine upload`. |
| `403` / invalid token | Regenerate token; update `PYPI_API_TOKEN` on environment `pypi`. |
| Name already taken | Pick another PyPI name and change `name` in `pyproject.toml`. |
| Release workflow skipped | Tag must match `v*` (e.g. `v0.1.0`), not `0.1.0`. |
| Environment missing | Create **`pypi`** under Settings → Environments. |

## Local smoke test (optional)

```bash
pip install build twine
python -m build
# twine upload dist/*   # only if testing token locally; prefer CI tag push
```
