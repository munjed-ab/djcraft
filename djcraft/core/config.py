# config.py
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ProjectStructureDefaultSettings:
    core_location: str = 'root'
    core_path: str = 'core'
    settings_structure: str = 'folder'
    required_folders: List[str] = field(default_factory=lambda: ['static', 'media', 'templates'])
    docs_dir: str = 'docs'

@dataclass
class FilesDefaultSettings:
    project: List[str] = field(default_factory=lambda: ['manage.py', '.gitignore', 'README.md', 'requirements.txt'])
    core: List[str] = field(default_factory=lambda: ['__init__.py', 'urls.py', 'wsgi.py', 'asgi.py'])
    core_settings: List[str] = field(default_factory=lambda: ['base.py', 'dev.py', 'prod.py', '__init__.py'])
    app: List[str] = field(default_factory=lambda: ['__init__.py', 'admin.py', 'apps.py', 'models.py', 'views.py', 'urls.py'])
    app_subdirectories: List[str] = field(default_factory=lambda: ['migrations', 'tests'])
    docker: List[str] = field(default_factory=lambda: ['Dockerfile', 'docker-compose.yml', '.dockerignore'])
    celery: List[str] = field(default_factory=lambda: ['celery.py'])
    auth: List[str] = field(default_factory=lambda: [
        'models.py', 'admin.py', 'apps.py', '__init__.py',
        'migrations/__init__.py', 'tests/__init__.py', 'tests/test_models.py'
    ])
    rest_api: List[str] = field(default_factory=lambda: ['api_urls.py'])
    db_router: List[str] = field(default_factory=lambda: ['router.py'])

@dataclass
class TemplateDefaultSettings:
    template_engine: str = 'jinja2'
    template_ext: str = '.template'
    template_dir: str = os.path.join(Path(__file__).parent.parent, 'templates')

@dataclass
class DjangoDefaultsSettings:
    default_apps: List[str] = field(default_factory=lambda: [
        'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
        'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles'
    ])
    default_middleware: List[str] = field(default_factory=lambda: [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware'
    ])

@dataclass
class ServiceOption:
    description: str
    dependencies: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)
    default_options: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AvailableServices:
    docker: ServiceOption = field(default_factory=lambda: ServiceOption(
        description='Docker configuration for containerization',
        options={'python_version': ['3.8', '3.9', '3.10', '3.11'], 'postgres_version': ['13', '14', '15']},
        default_options={'python_version': '3.9', 'postgres_version': '13'}
    ))
    celery: ServiceOption = field(default_factory=lambda: ServiceOption(
        description='Celery for asynchronous task processing',
        dependencies=['redis'],
        options={'broker': ['redis', 'rabbitmq'], 'use_flower': [True, False]},
        default_options={'broker': 'redis', 'use_flower': False}
    ))
    redis: ServiceOption = field(default_factory=lambda: ServiceOption(
        description='Redis for caching and messaging',
        options={'use_for_cache': [True, False], 'use_for_sessions': [True, False], 'host': 'str', 'port': 'int'},
        default_options={'use_for_cache': True, 'use_for_sessions': True, 'host': 'redis', 'port': 6379}
    ))
    authentication: ServiceOption = field(default_factory=lambda: ServiceOption(
        description='Authentication methods and user management',
        options={'custom_user': [True, False]},
        default_options={'custom_user': True, 'custom_user_app_name': 'users', 'custom_user_app_directory': ''}
    ))
    rest_api: ServiceOption = field(default_factory=lambda: ServiceOption(
        description='REST API setup with Django REST Framework',
        options={'framework': ['drf']},
        default_options={'framework': 'drf'}
    ))
    db_router: ServiceOption = field(default_factory=lambda: ServiceOption(
        description='Database router for multi-database setup',
        options={'db_types': ['postgres', 'mysql', 'sqlite']},
        default_options={'app_routing_map': {}, 'db_types': ['postgres']}
    ))

    def get_service_names(self) -> List[str]:
        return list(self.__dataclass_fields__.keys())

@dataclass
class CliDefaultSettings:
    project_name: str = 'myproject'
    apps: List[str] = field(default_factory=list)
    use_docker: bool = True
    use_celery: bool = False
    use_redis: bool = False
    use_whitenoise: bool = False
    env: str = 'dev'


class DefaultSettings:
    """Configuration settings for the Django boilerplate generator."""

    PROJECT_STRUCTURE = ProjectStructureDefaultSettings()
    DEFAULT_FILES = FilesDefaultSettings()
    TEMPLATE_CONFIG = TemplateDefaultSettings()
    DJANGO_DEFAULTS = DjangoDefaultsSettings()
    AVAILABLE_SERVICES = AvailableServices()
    CLI_DEFAULTS = CliDefaultSettings()
    
    @classmethod
    def get_service_info(cls, service_name: str) -> Optional[ServiceOption]:
        """Get service info by name."""
        if hasattr(cls.AVAILABLE_SERVICES, service_name):
            return getattr(cls.AVAILABLE_SERVICES, service_name)
        return None
    
    @classmethod
    def get_service_dependencies(cls, service_name: str) -> List[str]:
        """Get service dependencies by name."""
        service = cls.get_service_info(service_name)
        return service.dependencies if service else []
    
    @classmethod
    def get_service_default_options(cls, service_name: str) -> Dict[str, Any]:
        """Get default options for a service."""
        service = cls.get_service_info(service_name)
        return service.default_options if service else {}
