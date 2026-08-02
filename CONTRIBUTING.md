# Contributing to OpenCode for Home Assistant

Thanks for taking the time to contribute! 🎉

## Reporting Issues

Before opening an issue, please:

1. Check the [existing issues](https://github.com/pranjal-joshi/opencode/issues) for a similar report.
2. Use the provided [issue templates](.github/ISSUE_TEMPLATE/).
3. Include your Home Assistant version, HACS version, and relevant log snippets.

## Development Setup

We use the [Home Assistant devcontainer](https://developers.home-assistant.io/docs/development_environment/) flow.

1. Clone the repository.
2. Open it in VS Code using the devcontainer.
3. Run `scripts/setup` to install dependencies and pre-commit hooks.
4. Run `scripts/lint` and `scripts/develop` to validate your changes.

## Code Style

- Python 3.12+, `ruff` for linting, `black` for formatting (88 char lines).
- Follow the [Home Assistant coding guidelines](https://developers.home-assistant.io/docs/development_guidelines/).
- Keep `custom_components/opencode` self-contained; do not add unused dependencies.

## Testing

Add or update tests under `tests/` using `pytest-homeassistant-custom-component`. Run with:

```bash
python -m pytest
```

## Submitting Changes

1. Create a feature branch from `main`.
2. Make your changes and run `scripts/lint` + `scripts/develop`.
3. Open a Pull Request and fill out the template.

## License

By contributing you agree that your contributions will be licensed under the MIT License (see [LICENSE](LICENSE)).
