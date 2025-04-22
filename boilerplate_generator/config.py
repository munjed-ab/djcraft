import os
from pathlib import Path

class Config:
    DEFAULT_PROJECT_STRUCTURE = {
        'apps_dir': 'apps',
        'core_location': 'outside',  # 'inside' or 'outside' apps_dir
        'settings_structure': 'folder',  # 'single' or 'folder'
        'required_folders': ['static', 'media', 'templates'],
        'docs_dir': 'docs',
    }

    DEFAULT_FILES = {
        'project': [
            'manage.py',
            '.gitignore',
            'README.md',
            'requirements.txt',
        ],
        'core': [
            '__init__.py',
            'urls.py',
            'wsgi.py',
            'asgi.py',
        ],
        'app': [
            '__init__.py',
            'admin.py',
            'apps.py',
            'models.py',
            'views.py',
            'urls.py',
        ],
        'docker': [
            'Dockerfile',
        ],
    }

    TEMPLATE_CONFIG = {
        'template_engine': 'jinja2',  # 'string' or 'jinja2'
        'template_ext': '.template',
        'template_dir': os.path.join(Path(__file__).parent, 'templates'),
    }

    DJANGO_DEFAULTS = {
        'default_apps': [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
        ],
        'default_middleware': [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ],
    }

    DOCKER_DEFAULTS = {
        'python_version': '3.9',
        'postgres_version': '13',
        'default_services': ['web', 'db'],
    }

    CLI_DEFAULTS = {
        'project_name': 'myproject',
        'apps': [],
        'use_docker': True,
        'use_celery': False,
        'use_redis': False,
        'use_whitenoise': False,
    }

    @classmethod
    def get_template_path(cls, template_type):
        """Get absolute path to template directory"""
        return os.path.join(cls.TEMPLATE_CONFIG['template_dir'], template_type)

    @classmethod
    def get_project_structure(cls, custom_config=None):
        """Merge custom config with defaults"""
        config = cls.DEFAULT_PROJECT_STRUCTURE.copy()
        if custom_config:
            config.update(custom_config)
        return config

class ValidationRules:
    PROJECT_NAME_REGEX = r'^[a-zA-Z][a-zA-Z0-9_]+$'
    APP_NAME_REGEX = r'^[a-z][a-z0-9_]+$'

    @classmethod
    def is_valid_project_name(cls, name):
        import re
        return bool(re.match(cls.PROJECT_NAME_REGEX, name))

    @classmethod
    def is_valid_app_name(cls, name):
        import re
        return bool(re.match(cls.APP_NAME_REGEX, name))