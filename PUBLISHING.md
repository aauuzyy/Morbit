# Publishing Morbit to PyPI

Morbit's PyPI distribution name is `morbit`, its Python import package is `morbit`, and its command-line entry point is `morbit`.

## Recommended: GitHub Trusted Publishing

The repository includes `.github/workflows/publish.yml`. To use it:

1. Push the repository to GitHub.
2. On PyPI, create a Trusted Publisher for project `morbit`.
3. Enter your exact GitHub owner and repository name, workflow filename `publish.yml`, and environment name `pypi`.
4. Create a GitHub release to trigger publishing. The workflow can also be started manually from the GitHub Actions tab after the Trusted Publisher is configured.

The workflow builds the wheel and source distribution, then publishes with OpenID Connect. No long-lived PyPI API token needs to be stored in the repository.

## Build and validate locally

Run these commands from the repository root, where `pyproject.toml` is located:

```bash
python -m pip install --upgrade build twine
python -m unittest discover -s tests -v
python -m build
python -m twine check dist/*
```

Review the generated files in `dist/` before publishing. Never publish a release until the tests and runtime-loader checks pass.

## Optional: manual upload

You can upload to TestPyPI first:

```bash
python -m twine upload --repository testpypi dist/*
```

For production PyPI, use an API token through Twine only if you are not using Trusted Publishing:

```bash
python -m twine upload dist/*
```

Never put API tokens in the repository or commit them to source control.

## Future releases

Update `version` in `pyproject.toml` and `__version__` in `src/morbit/__init__.py` before building a new release. Keep those versions synchronized. PyPI does not allow replacing files for an already-published version; publish a new version instead.
