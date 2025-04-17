## Setup

```
poetry install
poetry shell
```

## Example Usage

```
poetry run python -m boilerplate_generator.cli myproject `
--apps users products blog `
--core-location outside `
--docker `
--celery `
--redis
```
