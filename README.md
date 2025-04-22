## Setup

```
poetry install
poetry shell
```

## Example Usage

# Interactive mode:

```
cd boilerplate_generator
poetry run python cli.py interactive
```

# V1

```
poetry run python -m boilerplate_generator.cli myproject `
--apps users products blog `
--core-location root `
--docker `
--celery `
--redis
```
