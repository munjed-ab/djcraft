import os
from pathlib import Path
from typing import Dict, List


class Config:
    """Configuration settings for the Django boilerplate generator."""
    
    DEFAULT_PROJECT_STRUCTURE = {
        'core_location': 'root',  # 'root', or 'custom'
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
            'docker-compose.yml',
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

    AVAILABLE_SERVICES = {
        'docker': {
            'description': 'Docker configuration for containerization',
            'dependencies': [],
            'options': {
                'python_version': ['3.8', '3.9', '3.10', '3.11'],
                'default_services': ['web', 'db']
            },
            'default_options': {
                'python_version': '3.9',
                'postgres_version': '13'
            }
        },
        'celery': {
            'description': 'Celery for asynchronous task processing',
            'dependencies': ['redis'],
            'options': {
                'broker': ['redis', 'rabbitmq'],
                'use_flower': [True, False]
            },
            'default_options': {
                'broker': 'redis',
                'use_flower': False
            }
        },
        'redis': {
            'description': 'Redis for caching and messaging',
            'dependencies': [],
            'options': {
                'use_for_cache': [True, False],
                'use_for_sessions': [True, False]
            },
            'default_options': {
                'use_for_cache': True,
                'use_for_sessions': True
            }
        },
        'authentication': {
            'description': 'Authentication methods and user management',
            'dependencies': [],
            'options': {
                'method': ['jwt', 'session', 'oauth'],
                'social_providers': ['google', 'facebook', 'twitter', 'github']
            },
            'default_options': {
                'method': 'session',
                'social_providers': []
            }
        },
        'rest_api': {
            'description': 'REST API setup with Django REST Framework',
            'dependencies': [],
            'options': {
                'versioning': [True, False],
                'swagger': [True, False],
                'throttling': [True, False]
            },
            'default_options': {
                'versioning': True,
                'swagger': True,
                'throttling': False
            }
        },
        'db_router': {
            'description': 'Database router for multi-database setup',
            'dependencies': [],
            'options': {
                'db_types': ['postgres', 'mysql', 'sqlite']
            },
            'default_options': {
                'db_types': ['postgres']
            }
        }
    }

    CLI_DEFAULTS = {
        'project_name': 'myproject',
        'apps': [],
        'use_docker': True,
        'use_celery': False,
        'use_redis': False,
        'use_whitenoise': False,
        'env': 'dev'
    }

    @classmethod
    def get_template_path(cls, template_type: str) -> str:
        """Get absolute path to template directory"""
        return os.path.join(cls.TEMPLATE_CONFIG['template_dir'], template_type)

    @classmethod
    def get_project_structure(cls, custom_config: Dict = None) -> Dict:
        """Merge custom config with defaults"""
        config = cls.DEFAULT_PROJECT_STRUCTURE.copy()
        if custom_config:
            config.update(custom_config)
        return config
    
    @classmethod
    def get_service_info(cls, service_name: str) -> Dict:
        """Get information about a service"""
        if service_name not in cls.AVAILABLE_SERVICES:
            raise ValueError(f"Unknown service: {service_name}")
        return cls.AVAILABLE_SERVICES[service_name]
    
    @classmethod
    def get_service_dependencies(cls, service_name: str) -> List[str]:
        """Get dependencies for a service"""
        if service_name not in cls.AVAILABLE_SERVICES:
            return []
        return cls.AVAILABLE_SERVICES[service_name]['dependencies']