import os
from pathlib import Path
from typing import Dict, List, Optional

from config import Config
from exceptions import DependencyError, TemplateRenderError
from jinja2 import Environment, FileSystemLoader
from project_structure_manager import ProjectStructureManager


class DjangoProjectGenerator:
    """
    Generates Django project files based on a project structure definition.
    """
    def __init__(self, structure_manager: ProjectStructureManager):
        """
        Initialize the generator with a project structure
        
        Args:
            structure_manager: Project structure manager with defined structure
        """
        self.structure = structure_manager
        self.project_name = structure_manager.project_name
        self.project_path = structure_manager.project_path
        self.template_env = self._setup_template_env()
        
    def _setup_template_env(self) -> Environment:
        """Set up Jinja2 environment for templates"""
        template_dir = Config.TEMPLATE_CONFIG['template_dir']
        return Environment(loader=FileSystemLoader(template_dir))
    
    def generate_project(self) -> None:
        """
        Generate the entire project based on the defined structure
        """
        # Validate structure
        errors = self.structure.validate_structure()
        if errors:
            raise ValueError(f"Invalid project structure: {', '.join(errors)}")
        
        # project directory
        self.project_path.mkdir(exist_ok=True)
        
        # directoriess structure
        self._create_directories()
        
        # core files
        self._generate_core_files()
        
        # apps
        self._generate_apps()
        
        # service configurations
        self._generate_service_configs()
        
        # base project files
        self._generate_base_project_files()
        
        print(f"Successfully generated Django project: {self.project_name}")
    
    def _create_directories(self) -> None:
        """Create all directories defined in the structure"""
        for folder in Config.DEFAULT_PROJECT_STRUCTURE['required_folders']:
            (self.project_path / folder).mkdir(exist_ok=True)
        
        for dir_path in self.structure.structure['directories']:
            full_dir_path = self.project_path / dir_path
            full_dir_path.mkdir(parents=True, exist_ok=True)
    
    def _generate_core_files(self) -> None:
        """Generate core Django project files"""
        core_path = self.structure.get_core_path()
        core_path.mkdir(parents=True, exist_ok=True)
        
        settings_dir = core_path / 'settings'
        settings_dir.mkdir(exist_ok=True)
        
        for file in Config.DEFAULT_FILES['core']:
            if file == '__init__.py':
                self._render_template(
                    'project_template/core/__init__.py.template',
                    core_path / file,
                    {'use_celery': self.structure.has_service('celery')}
                )
            else:
                template_name = f'project_template/core/{file}.template'
                self._render_template(
                    template_name,
                    core_path / file,
                    {
                        'project_name': self.project_name,
                        'core_path': str(core_path).replace('\\', '/'),
                        'imports': self.structure.get_python_import_paths()
                    }
                )
        
        self._generate_settings_files(settings_dir)
    
    def _generate_settings_files(self, settings_dir: Path) -> None:
        """Generate Django settings files"""
        # base settings
        import_paths = self.structure.get_python_import_paths()
        apps_imports = ",\n    ".join([f"'{path}'" for path in import_paths.values()])
        
        parent_dir = ""
        if self.structure.structure['core']['location'] == 'inside':
            parent_dir = ".parent"
            
        self._render_template(
            'project_template/core/settings/base.py.template',
            settings_dir / 'base.py',
            {
                'parent_dir': parent_dir,
                'apps_imports': apps_imports,
                'core_path': str(self.structure.structure['core']['path']).replace('/', '.'),
                'default_apps': Config.DJANGO_DEFAULTS['default_apps'],
                'middleware': Config.DJANGO_DEFAULTS['default_middleware']
            }
        )
        
        static_media_settings = """
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
"""
        
        for env in ['dev', 'prod']:
            self._render_template(
                f'project_template/core/settings/{env}.py.template',
                settings_dir / f'{env}.py',
                {
                    'core_path': str(self.structure.structure['core']['path']).replace('/', '.'),
                    'static_media_settings': static_media_settings
                }
            )
        
        self._render_template(
            'project_template/core/settings/__init__.py.template',
            settings_dir / '__init__.py',
            {'env': self.structure.structure.get('env', 'dev')}
        )
    
    def _generate_apps(self) -> None:
        """Generate all app directories and files"""
        for app_name, app_path in self.structure.structure['apps'].items():
            app_dir = self.project_path / app_path
            app_dir.mkdir(parents=True, exist_ok=True)
            
            for file in Config.DEFAULT_FILES['app']:
                self._render_template(
                    f'app_template/{file}.template',
                    app_dir / file,
                    {
                        'app_name': app_name,
                        'app_path': app_path.replace('/', '.')
                    }
                )
            
            migrations_dir = app_dir / 'migrations'
            migrations_dir.mkdir(exist_ok=True)
            self._render_template(
                'app_template/migrations/__init__.py.template',
                migrations_dir / '__init__.py'
            )
            
            tests_dir = app_dir / 'tests'
            tests_dir.mkdir(exist_ok=True)
            self._render_template(
                'app_template/tests/test_models.py.template',
                tests_dir / 'test_models.py'
            )
            self._render_template(
                'app_template/tests/__init__.py.template',
                tests_dir / '__init__.py'
            )
    
    def _generate_service_configs(self) -> None:
        """Generate configuration for all specified services"""
        for service in self.structure.structure['services']:
            service_name = service['name']
            options = service['options']
            
            self._check_service_dependencies(service_name)
            
            if service_name == 'docker':
                self._generate_docker_config(options)
            elif service_name == 'celery':
                self._generate_celery_config(options)
            elif service_name == 'redis':
                self._generate_redis_config(options)
            elif service_name == 'authentication':
                self._generate_auth_config(options)
            elif service_name == 'rest_api':
                self._generate_rest_api_config(options)
            elif service_name == 'db_router':
                self._generate_db_router_config(options)
    
    def _check_service_dependencies(self, service_name: str) -> None:
        """
        Check if all dependencies for a service are included
        
        Args:
            service_name: Name of the service to check
        """
        dependencies = Config.get_service_dependencies(service_name)
        existing_services = [s['name'] for s in self.structure.structure['services']]
        
        for dep in dependencies:
            if dep not in existing_services:
                raise DependencyError(
                    f"Service '{service_name}' requires '{dep}' which is not included"
                )
            
    def _generate_docker_config(self, options: Dict) -> None:
        """Generate Docker configuration files"""
        docker_dir = self.project_path / 'docker'
        docker_dir.mkdir(exist_ok=True)
        
        services = [s['name'] for s in self.structure.structure['services']]
        
        python_version = options.get('python_version', '3.9')
        postgres_version = options.get('postgres_version', '13')
        
        # Dockerfile
        self._render_template(
            'docker_template/Dockerfile.template',
            docker_dir / 'Dockerfile',
            {
                'python_version': python_version,
                'project_name': self.project_name
            }
        )
        
        # docker-compose.yml
        use_celery = 'celery' in services
        use_redis = 'redis' in services
        
        self._render_template(
            'docker_template/docker-compose.yml.template',
            self.project_path / 'docker-compose.yml',
            {
                'project_name': self.project_name,
                'postgres_version': postgres_version,
                'use_celery': use_celery,
                'use_redis': use_redis
            }
        )
        
        # .dockerignore
        self._render_template(
            'docker_template/.dockerignore.template',
            self.project_path / '.dockerignore'
        )
    
    def _generate_celery_config(self, options: Dict) -> None:
        """Generate Celery configuration files"""
        core_path = self.structure.get_core_path()
        
        self._render_template(
            'project_template/core/celery.py.template',
            core_path / 'celery.py',
            {
                'project_name': self.project_name,
                'core_path': str(self.structure.structure['core']['path']).replace('/', '.')
            }
        )
        
        init_path = core_path / '__init__.py'
        celery_import = "\n# Import Celery app\nfrom .celery import app as celery_app\n\n__all__ = ('celery_app',)"
        
        if init_path.exists():
            with open(init_path, 'r') as f:
                content = f.read()
            
            if 'celery_app' not in content:
                with open(init_path, 'w') as f:
                    f.write(content + celery_import)
        else:
            with open(init_path, 'w') as f:
                f.write(celery_import)
        
        settings_path = core_path / 'settings' / 'base.py'
        
        if settings_path.exists():
            # broker options
            broker = options.get('broker', 'redis')
            broker_url = "redis://redis:6379/0" if broker == 'redis' else "amqp://guest:guest@rabbitmq:5672//"
            
            celery_settings = f"""
# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', '{broker_url}')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', '{broker_url}')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
"""
            
            with open(settings_path, 'r') as f:
                content = f.read()
            
            if 'CELERY_BROKER_URL' not in content:
                with open(settings_path, 'a') as f:
                    f.write("\n" + celery_settings)
        
        # add celery to requirements
        self._add_to_requirements([
            'celery>=5.2.0',
            'django-celery-results>=2.4.0'
        ])
    
    def _generate_redis_config(self, options: Dict) -> None:
        """Generate Redis configuration"""
        core_path = self.structure.get_core_path()
        settings_path = core_path / 'settings' / 'base.py'
        
        use_for_cache = options.get('use_for_cache', True)
        use_for_sessions = options.get('use_for_sessions', True)
        
        if settings_path.exists():
            redis_settings = """
# Redis Configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/1')
"""
            
            if use_for_cache:
                redis_settings += """
# Redis Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
"""
            
            if use_for_sessions:
                redis_settings += """
# Redis Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
"""
            
            with open(settings_path, 'r') as f:
                content = f.read()
            
            if 'REDIS_URL' not in content:
                with open(settings_path, 'a') as f:
                    f.write("\n" + redis_settings)
        
        # add redis to requirements
        self._add_to_requirements([
            'django-redis>=5.2.0',
            'redis>=4.3.4'
        ])
    
    def _generate_auth_config(self, options: Dict) -> None:
        """Generate authentication configuration"""
        # Get authentication method
        auth_method = options.get('method', 'session')
        social_providers = options.get('social_providers', [])
        
        # add required packages to requirements
        required_packages = ['django-allauth>=0.50.0']
        
        if auth_method == 'jwt':
            required_packages.append('djangorestframework-simplejwt>=5.2.0')
        elif auth_method == 'oauth':
            required_packages.append('django-oauth-toolkit>=2.1.0')
        
        # add social auth providers if needed
        if social_providers:
            required_packages.append('django-allauth>=0.50.0')  # Ensure allauth is included
            
        self._add_to_requirements(required_packages)
        
        # creat auth app if it doesn't exist already
        if 'authentication' not in self.structure.structure['apps']:
            auth_app_dir = self.project_path / 'authentication'
            auth_app_dir.mkdir(exist_ok=True)
            
            # create basic auth app files
            for file in Config.DEFAULT_FILES['app']:
                self._render_template(
                    f'app_template/{file}.template',
                    auth_app_dir / file,
                    {'app_name': 'authentication'}
                )
            
            # Create migrations directory
            migrations_dir = auth_app_dir / 'migrations'
            migrations_dir.mkdir(exist_ok=True)
            self._render_template(
                'app_template/migrations/__init__.py.template',
                migrations_dir / '__init__.py'
            )
            
            # create custom models and views based on auth method
            self._render_template(
                f'auth_template/models_{auth_method}.py.template',
                auth_app_dir / 'models.py',
                {'social_providers': social_providers}
            )
            
            self._render_template(
                f'auth_template/views_{auth_method}.py.template',
                auth_app_dir / 'views.py',
                {'social_providers': social_providers}
            )
            
            self._render_template(
                f'auth_template/urls_{auth_method}.py.template',
                auth_app_dir / 'urls.py',
                {'social_providers': social_providers}
            )
            
            # add auth app to structure
            self.structure.structure['apps']['authentication'] = 'authentication'
        
        # Update settings
        core_path = self.structure.get_core_path()
        settings_path = core_path / 'settings' / 'base.py'
        
        if settings_path.exists():
            auth_settings = """
# Authentication Configuration
"""
            
            if auth_method == 'jwt':
                auth_settings += """
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
}
"""
            elif auth_method == 'oauth':
                auth_settings += """
OAUTH2_PROVIDER = {
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope'},
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ),
}
"""
            
            # add allauth settings if using social providers
            if social_providers:
                auth_settings += """
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

INSTALLED_APPS += [
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
"""
                # add specific provider apps
                for provider in social_providers:
                    auth_settings += f"    'allauth.socialaccount.providers.{provider}',\n"
                
                auth_settings += "]\n"
                
                auth_settings += """
SITE_ID = 1

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
"""
            
            # add imports at the top if needed
            imports_to_add = []
            if auth_method == 'jwt':
                imports_to_add.append("from datetime import timedelta")
            
            # updarte the settings file
            with open(settings_path, 'r') as f:
                content = f.read()
            
            # add imports if needed
            if imports_to_add and not any(imp in content for imp in imports_to_add):
                import_block = "\n".join(imports_to_add) + "\n\n"
                content = import_block + content
            
            # add auth settings if not already there
            if auth_method not in content:
                with open(settings_path, 'w') as f:
                    f.write(content + "\n" + auth_settings)
    
    def _generate_rest_api_config(self, options: Dict) -> None:
        """Generate REST API configuration"""
        versioning = options.get('versioning', True)
        swagger = options.get('swagger', True)
        throttling = options.get('throttling', False)
        
        required_packages = ['djangorestframework>=3.14.0']
        
        if swagger:
            required_packages.append('drf-yasg>=1.21.4')
        
        self._add_to_requirements(required_packages)
        
        if 'api' not in self.structure.structure['apps']:
            api_app_dir = self.project_path / 'api'
            api_app_dir.mkdir(exist_ok=True)
            
            for file in Config.DEFAULT_FILES['app']:
                self._render_template(
                    f'app_template/{file}.template',
                    api_app_dir / file,
                    {'app_name': 'api'}
                )
            
            migrations_dir = api_app_dir / 'migrations'
            migrations_dir.mkdir(exist_ok=True)
            self._render_template(
                'app_template/migrations/__init__.py.template',
                migrations_dir / '__init__.py'
            )
            
            if versioning:
                for version in ['v1']:
                    version_dir = api_app_dir / version
                    version_dir.mkdir(exist_ok=True)
                    
                    self._render_template(
                        'app_template/__init__.py.template',
                        version_dir / '__init__.py'
                    )
                    
                    self._render_template(
                        'api_template/version_urls.py.template',
                        version_dir / 'urls.py',
                        {'version': version}
                    )
            
            self._render_template(
                'api_template/urls.py.template',
                api_app_dir / 'urls.py',
                {
                    'versioning': versioning,
                    'swagger': swagger
                }
            )
            
            self.structure.structure['apps']['api'] = 'api'

        core_path = self.structure.get_core_path()
        settings_path = core_path / 'settings' / 'base.py'
        
        if settings_path.exists():
            api_settings = """
# REST Framework Configuration
REST_FRAMEWORK = {
"""
            
            if versioning:
                api_settings += """
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1'],
"""
            
            if throttling:
                api_settings += """
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    },
"""
            
            api_settings += "}\n"
            
            if swagger:
                api_settings += """
# Swagger/OpenAPI Documentation
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    }
}
"""
            installed_apps = "\nINSTALLED_APPS += [\n    'rest_framework',\n"
            
            if swagger:
                installed_apps += "    'drf_yasg',\n"
                
            installed_apps += "]\n"
            with open(settings_path, 'r') as f:
                content = f.read()
            
            if 'rest_framework' not in content:
                with open(settings_path, 'a') as f:
                    f.write(installed_apps + api_settings)
    
    def _generate_db_router_config(self, options: Dict) -> None:
        """Generate database router configuration"""
        db_types = options.get('db_types', ['postgres'])
        db_dir = self.project_path / 'database'
        db_dir.mkdir(exist_ok=True)
        self._render_template(
            'db_template/router.py.template',
            db_dir / 'router.py',
            {'db_types': db_types}
        )
        
        self._render_template(
            'db_template/__init__.py.template',
            db_dir / '__init__.py'
        )
        core_path = self.structure.get_core_path()
        settings_path = core_path / 'settings' / 'base.py'
        
        if settings_path.exists():
            db_settings = """
# Multiple Database Configuration
DATABASE_ROUTERS = ['database.router.DatabaseRouter']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'django'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    },
"""
            for db_type in db_types:
                if db_type == 'postgres' and len(db_types) > 1:
                    db_settings += """
    'postgres': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB_NAME', 'django_secondary'),
        'USER': os.environ.get('POSTGRES_DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('POSTGRES_DB_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_DB_PORT', '5432'),
    },
"""
                elif db_type == 'mysql':
                    db_settings += """
    'mysql': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_DB_NAME', 'django_mysql'),
        'USER': os.environ.get('MYSQL_DB_USER', 'mysql'),
        'PASSWORD': os.environ.get('MYSQL_DB_PASSWORD', 'mysql'),
        'HOST': os.environ.get('MYSQL_DB_HOST', 'localhost'),
        'PORT': os.environ.get('MYSQL_DB_PORT', '3306'),
    },
"""
                elif db_type == 'sqlite':
                    db_settings += """
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    },
"""
            db_settings += "}\n"
            required_packages = []
            
            if 'postgres' in db_types:
                required_packages.append('psycopg2-binary>=2.9.3')
            if 'mysql' in db_types:
                required_packages.append('mysqlclient>=2.1.0')
                
            self._add_to_requirements(required_packages)

            with open(settings_path, 'r') as f:
                content = f.read()
            
            if 'DATABASE_ROUTERS' not in content:
                if 'DATABASES = {' in content:
                    content = content.replace(
                        "DATABASES = {\n    'default': {\n        'ENGINE': 'django.db.backends.sqlite3',\n        'NAME': BASE_DIR / 'db.sqlite3',\n    }\n}",
                        db_settings
                    )
                else:
                    content += "\n" + db_settings
                    
                with open(settings_path, 'w') as f:
                    f.write(content)
    
    def _generate_base_project_files(self) -> None:
        """Generate base project files like manage.py, README, etc."""
        core_import_path = str(self.structure.structure['core']['path']).replace('/', '.')
        
        self._render_template(
            'project_template/manage.py.template',
            self.project_path / 'manage.py',
            {'core_path': core_import_path}
        )
        
        manage_py = self.project_path / 'manage.py'
        manage_py.chmod(manage_py.stat().st_mode | 0o111)
        
        self._render_template(
            'project_template/.gitignore.template',
            self.project_path / '.gitignore'
        )
        
        services = [s['name'] for s in self.structure.structure['services']]
        
        self._render_template(
            'project_template/README.md.template',
            self.project_path / 'README.md',
            {
                'project_name': self.project_name,
                'apps': list(self.structure.structure['apps'].keys()),
                'use_docker': 'docker' in services,
                'use_celery': 'celery' in services,
                'use_redis': 'redis' in services,
                'use_rest_api': 'rest_api' in services,
                'core_location': self.structure.structure['core']['location']
            }
        )
        
        requirements_path = self.project_path / 'requirements.txt'
        if not requirements_path.exists():
            self._render_template(
                'project_template/requirements.txt.template',
                requirements_path
            )
    
    def _add_to_requirements(self, packages: List[str]) -> None:
        """
        Add packages to requirements.txt
        
        Args:
            packages: List of packages to add
        """
        requirements_path = self.project_path / 'requirements.txt'
        
        existing_content = ""
        if requirements_path.exists():
            with open(requirements_path, 'r') as f:
                existing_content = f.read()
        
        with open(requirements_path, 'a') as f:
            for package in packages:
                if package not in existing_content:
                    f.write(f"{package}\n")
    
    def _render_template(self, template_name: str, output_path: Path, context: Optional[Dict] = None) -> None:
        """
        Render a template with the given context
        
        Args:
            template_name: Name of the template file
            output_path: Path where to write the rendered template
            context: Template context data
        """
        context = context or {}
        template_ext = Config.TEMPLATE_CONFIG['template_ext']
        
        # make sure template has the .template extension
        if not template_name.endswith(template_ext) and not os.path.exists(
            os.path.join(Config.TEMPLATE_CONFIG['template_dir'], template_name)
        ):
            template_name += template_ext
        
        try:
            # get the template
            template = self.template_env.get_template(template_name)
            
            rendered = template.render(**context)
            
            # create parent directories if they don't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # write the rendered template to file
            with open(output_path, 'w') as f:
                f.write(rendered)
                
        except Exception as e:
            raise TemplateRenderError(f"Error rendering template '{template_name}': {e}")