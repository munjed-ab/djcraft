## Setup

```
pip3 install poetry or apt install python3-poetry
poetry install
poetry shell
```

## Example Usage

# Interactive mode:

```
cd djcraft
poetry run python main.py interactive
or
python main.py interactive
```

# Genaerate mode:

```
cd djcraft
poetry run python main.py generate newproject_config.yaml
```

# djcraft a Django Boilerplate Generator

A CLI tool for generating Django project boilerplates with customizable structures, flexible directory layouts, and built-in support for common services like Docker, Celery, and Redis.

## Features

-  **Flexible Project Structures** - Place apps anywhere: root level, nested directories, or custom layouts
-  **Multiple App Types** - Standard, REST API, and Authentication apps with appropriate files
-  **Service Integration** - Built-in support for Docker, Celery, Redis, and more
-  **Template-Based Generation** - Jinja2 templates for easy customization
-  **Configuration-Driven** - Use YAML configs for reproducible project setups
-  **Interactive Mode** - User-friendly CLI for step-by-step project creation
-  **Automatic Dependencies** - Generates requirements.txt with all needed packages

## Installation

```bash
# Clone the repository
git clone https://github.com/munjed-ab/djcraft.git
# Install dependencies
poetry install
poetry shell

# Optional: Install Rich for better CLI experience
pip install rich
```

## Quick Start

### Interactive Mode (Recommended)

```bash
python main.py interactive
```

Follow the prompts to create your project structure.

### CLI Mode (Under Development)

```bash
# Basic project with apps at root level
python main.py create myproject --apps blog users --core-location root

# Project with nested structure
python main.py create myproject --apps blog users api --directory apps --core-location custom --core-path config

# Add services
python main.py create myproject --apps blog --docker --celery --redis
```

### YAML Configuration

Create a `project_config.yaml`:

```yaml
project_name: my_blog

# Core Django files location
core:
  location: root  # or 'custom'
  path: core      # if custom, specify path

# Define custom directories
directories:
  - name: apps
    parent: ""
  - name: api
    parent: apps

# Define Django apps
apps:
  - name: blog
    path: apps/blog
  - name: users
    path: apps/users
  - name: posts_api
    path: api/posts_api

# Services to include
services:
  - name: docker
    options:
      python_version: "3.11"
      postgres_version: "15"
  
  - name: celery
    options:
      broker: redis
      use_flower: true
  
  - name: redis
    options:
      use_for_cache: true
      use_for_sessions: true
  
  - name: rest_api
    options:
      framework: drf
```

Then generate:

```bash
python main.py generate project_config.yaml
```

## Project Structure Examples

### Simple Structure

```
myproject/
├── manage.py
├── requirements.txt
├── .gitignore
├── README.md
├── core/                    # Django core files
│   ├── __init__.py
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── dev.py
│       └── prod.py
├── blog/                    # Django app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── migrations/
│   └── tests/
└── users/                   # Django app
    ├── __init__.py
    ├── admin.py
    └── ...
```

### Nested Structure

```
myproject/
├── manage.py
├── config/                  # Core files in custom location
│   ├── __init__.py
│   ├── urls.py
│   └── settings/
├── apps/                    # Apps grouped together
│   ├── blog/
│   ├── users/
│   └── comments/
├── api/                     # API apps separated
│   ├── blog_api/
│   └── users_api/
├── static/
├── media/
└── templates/
```

## CLI Commands

### `create` - Create a New Project

```bash
python main.py create PROJECT_NAME [OPTIONS]

Options:
  --apps APP1 APP2 ...           List of Django apps to create
  --directory DIR                Place apps in this directory
  --core-location {root,custom}  Where to place core Django files
  --core-path PATH               Path for core files (if custom)
  --docker                       Include Docker configuration
  --celery                       Include Celery configuration
  --redis                        Include Redis configuration
  --rest-api                     Include Django REST Framework
  --db-router                    Include database router
```

### `interactive` - Interactive Project Creation

```bash
python main.py interactive
```

Guided interface for creating projects with all configuration options.

### `generate` - Generate from Config File

```bash
python main.py generate CONFIG_FILE.yaml
```

### `validate` - Validate Configuration

```bash
python main.py validate CONFIG_FILE.yaml
```

Check your configuration file for errors before generation.

## App Types

### Standard App
Default Django app with models, views, admin, urls.

```python
# Auto-detected for most app names
python main.py create myproject --apps blog products
```

### API App
Includes serializers and API views for REST endpoints.

```python
# Auto-detected for apps with 'api' in the name
python main.py create myproject --apps blog_api users_api
```

### Auth App
Includes custom user models and authentication forms.

```python
# Auto-detected for apps named: users, accounts, auth, authentication
python main.py create myproject --apps users
```

## Services (Under Development)

### Docker

Generates `Dockerfile` and `docker-compose.yml` with PostgreSQL, Redis, and your Django app.

```yaml
services:
  - name: docker
    options:
      python_version: "3.11"
      postgres_version: "15"
```

### Celery

Configures Celery for asynchronous task processing.

```yaml
services:
  - name: celery
    options:
      broker: redis        # or 'rabbitmq'
      use_flower: true     # Celery monitoring tool
```

### Redis

Sets up Redis for caching and sessions.

```yaml
services:
  - name: redis
    options:
      use_for_cache: true
      use_for_sessions: true
      host: redis
      port: 6379
```

### REST API

Configures Django REST Framework.

```yaml
services:
  - name: rest_api
    options:
      framework: drf
```

## Configuration System

The generator uses a layered configuration approach:

1. **Default Settings** (`core/config.py`) - Base configuration
2. **Runtime Config** (`core/runtime_config.py`) - YAML overrides
3. **Configuration Manager** (`core/configuration_manager.py`) - Merges all configs


## Troubleshooting

### Apps Not Generating

1. Check that templates exist in `templates/app_template/`
2. Verify configuration is properly loaded
3. Run with `--verbose` flag for detailed output
4. Check file permissions in output directory

### Template Rendering Errors

1. Ensure Jinja2 is installed: `pip install jinja2`
2. Check template syntax in `.template` files
3. Verify context variables match template expectations

### Service Dependencies Missing

Some services require others:
- Celery requires Redis (or RabbitMQ)
- Docker can include Redis and PostgreSQL automatically


## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Django project for the amazing framework
- Jinja2 for powerful templating
- Rich library for beautiful CLI output

---

**Built for internal team use at [Eleva]**
