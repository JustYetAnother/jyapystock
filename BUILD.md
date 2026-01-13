BUILD and PUBLISH instructions for jyapystock

This document explains how to build the package distributions and publish them to TestPyPI or PyPI.

Prerequisites
- Python 3.11+ and a virtual environment (project uses `.venv`).
- `build` and `twine` packages installed in the environment.

Recommended local steps

1. Activate your venv

```bash
source .venv/bin/activate
```

2. Install build tools

```bash
python -m pip install --upgrade pip build twine
```

3. Remove any previous versions and build source and wheel

```bash
rm -rf dist build *.egg-info
python -m build
# outputs are in dist/ e.g. dist/jyapystock-0.1.0-py3-none-any.whl
```

4. Validate distribution files

```bash
python -m twine check dist/*
```

Upload to TestPyPI (recommended step before real PyPI)

1. Create a TestPyPI API token at https://test.pypi.org/manage/account/ and copy it.
2. Upload using twine (recommended to use env vars):

```bash
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-<TEST-TOKEN>"
python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
# then unset
unset TWINE_PASSWORD
unset TWINE_USERNAME
```

3. Install from TestPyPI for smoke test:

```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps jyapystock
```

Publish to real PyPI

1. Create a PyPI API token at https://pypi.org/manage/account/#api-tokens and copy it.
2. Upload using twine:

```bash
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-<YOUR-PRODUCTION-TOKEN>"
python -m twine upload dist/*
# then unset
unset TWINE_PASSWORD
unset TWINE_USERNAME
```

Automation via GitHub Actions

- Add `PYPI_API_TOKEN` (or `ALPHAVANTAGE_API_KEY` if needed) to repository Secrets.
- Create a workflow that triggers on tag push and runs build + twine upload using the `TWINE_PASSWORD` environment variable set from the secret.

Example publish step snippet:

```yaml
- name: Publish to PyPI
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
  run: |
    python -m pip install --upgrade build twine
    python -m build
    python -m twine upload dist/*
```

Notes
- Ensure you bump the version in `pyproject.toml` before publishing; PyPI rejects duplicate versions.
- Keep tokens secret — add them to GitHub repository secrets for CI usage.
- Prefer TestPyPI for a smoke test before publishing to real PyPI.
