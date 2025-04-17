import argparse
from pathlib import Path
from typing import Dict, List, Optional

from .config import Config, ValidationRules
from .exceptions import InvalidAppNameError, InvalidProjectNameError


class DjangoBoilerplateGenerator:
    def __init__(
        self,
        project_name: str,
        apps: Optional[List[str]] = None,
        core_location: str = Config.DEFAULT_PROJECT_STRUCTURE['core_location'],
        use_docker: bool = Config.CLI_DEFAULTS['use_docker'],
        use_celery: bool = Config.CLI_DEFAULTS['use_celery'],
        use_redis: bool = Config.CLI_DEFAULTS['use_redis'],
        env: str = 'dev'
    ):
        self.project_name = project_name
        self.apps = apps or []
        self.core_location = core_location
        self.use_docker = use_docker
        self.use_celery = use_celery
        self.use_redis = use_redis
        self.env = env
        self.project_path = Path(project_name)
        self.core_path = self._get_core_path()

    def _get_core_path(self) -> str:
        """Determine core directory path based on configuration"""
        if self.core_location == 'inside':
            return f"{Config.DEFAULT_PROJECT_STRUCTURE['apps_dir']}/core"
        return 'core'

    def _get_core_full_path(self) -> Path:
        """Get the full path to the core directory"""
        return self.project_path / Path(self.core_path)

    def validate_inputs(self) -> None:
        """Validate project and app names"""
        if not ValidationRules.is_valid_project_name(self.project_name):
            raise InvalidProjectNameError(f"Invalid project name: {self.project_name}")
        
        for app in self.apps:
            if not ValidationRules.is_valid_app_name(app):
                raise InvalidAppNameError(f"Invalid app name: {app}")

    def generate_project(self) -> None:
        """Main method to generate the entire project structure"""
        self.validate_inputs()
        print("Validating...")
        self._create_base_structure()
        print("Creating base structure...")
        self._generate_core_files()
        print("Creating core files...")
        self._generate_apps()
        print("Generating apps...")
        
        if self.use_docker:
            self._generate_docker_files()
        
        if self.use_celery:
            print("WE USING CELERY")
            self._generate_celery_files()
        
        if self.use_redis:
            self._generate_redis_config()
        
        self._generate_readme()
        print(f"Successfully created Django project '{self.project_name}'")

    def _generate_celery_files(self) -> None:
        """Generate Celery configuration files"""
        print("Generating Celery files...")
        
        self._render_template(
            'project_template/core/celery.py.template',
            self._get_core_full_path() / 'celery.py',
            {
                'project_name': self.project_name,
                'core_path': self.core_path
            }
        )
        
        celery_import = "\n# Import Celery app\nfrom .celery import app as celery_app\n\n__all__ = ('celery_app',)"
        
        init_path = self._get_core_full_path() / '__init__.py'
        if init_path.exists():
            with open(init_path, 'r') as f:
                content = f.read()
            
            if 'celery_app' not in content:
                with open(init_path, 'w') as f:
                    f.write(content + celery_import)
        else:
            with open(init_path, 'w') as f:
                f.write(celery_import)
        
        settings_path = self._get_core_full_path() / 'settings' / 'base.py'
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                content = f.read()
            
            celery_settings = """
# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
"""
            
            if 'CELERY_BROKER_URL' not in content:
                with open(settings_path, 'a') as f:
                    f.write("\n" + celery_settings)

    def _generate_redis_config(self) -> None:
        """Generate Redis configuration in settings"""
        print("Configuring Redis...")
        
        settings_path = self._get_core_full_path() / 'settings' / 'base.py'
        if settings_path.exists():
            with open(settings_path, 'r') as f:
                content = f.read()
            
            redis_settings = """
# Redis Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
# Redis Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
"""
            
            if 'REDIS_URL' not in content:
                with open(settings_path, 'a') as f:
                    f.write("\n" + redis_settings)

        req_path = self.project_path / 'requirements.txt'
        redis_packages = [
            'django-redis>=5.2.0',
            'redis>=4.3.4'
        ]
        
        existing_content = ""
        if req_path.exists():
            with open(req_path, 'r') as f:
                existing_content = f.read()
        
        with open(req_path, 'a') as f:
            for package in redis_packages:
                if package not in existing_content:
                    f.write(f"{package}\n")

    def _generate_readme(self) -> None:
        """Generate project README.md file"""
        print("Generating README.md...")
        
        self._render_template(
            'project_template/README.md.template',
            self.project_path / 'README.md',
            {
                'project_name': self.project_name,
                'apps': self.apps,
                'use_docker': self.use_docker,
                'use_celery': self.use_celery,
                'use_redis': self.use_redis,
                'core_location': self.core_location
            }
        )

    def _create_base_structure(self) -> None:
        """Create the basic directory structure"""

        self.project_path.mkdir(exist_ok=True)
        
        if self.apps or self.core_location == 'inside':
            (self.project_path / Config.DEFAULT_PROJECT_STRUCTURE['apps_dir']).mkdir(exist_ok=True)

        self._get_core_full_path().mkdir(exist_ok=True)

        for folder in Config.DEFAULT_PROJECT_STRUCTURE['required_folders']:
            (self.project_path / folder).mkdir(exist_ok=True)

        for file in Config.DEFAULT_FILES['project']:
            self._render_template(
                f'project_template/{file}.template',
                self.project_path / file,
                {'core_path': self.core_path}
            )

    def _generate_core_files(self) -> None:
        """Generate all core project files"""
        settings_dir = self._get_core_full_path() / 'settings'
        settings_dir.mkdir(exist_ok=True)
        
        self._render_template(
            'project_template/core/__init__.py',
            self._get_core_full_path() / '__init__.py'
        )
        
        self._render_template(
            'project_template/core/urls.py',
            self._get_core_full_path() / 'urls.py',
            {
                'core_path': self.core_path,
                'apps': self.apps,
                'core_location': self.core_location
            }
        )
        
        self._render_template(
            'project_template/core/wsgi.py',
            self._get_core_full_path() / 'wsgi.py',
            {'core_path': self.core_path}
        )
        
        self._render_template(
            'project_template/core/asgi.py',
            self._get_core_full_path() / 'asgi.py',
            {'core_path': self.core_path}
        )
        
        if Config.DEFAULT_PROJECT_STRUCTURE['settings_structure'] == 'folder':
            self._generate_split_settings()
        else:
            self._generate_single_settings_file()# TODO:

    def _generate_docker_files(self) -> None:
        """Generate all core project files"""
        docker_dir = self.project_path / 'docker'
        docker_dir.mkdir(exist_ok=True)
        
        self._render_template(
            'docker_template/Dockerfile.template',
            docker_dir / 'Dockerfile'
        )

    def _generate_split_settings(self) -> None:
        """Generate the split settings configuration"""
        settings_dir = self._get_core_full_path() / 'settings'
        settings_dir.mkdir(exist_ok=True)
        
        parent_dir = ""
        if self.core_location == 'inside':
            parent_dir = ".parent"
        
        apps_imports = ""
        if self.apps:
            app_format = "'apps.{}'" if self.core_location == 'outside' else "'{}'"
            apps_imports = ",\n    ".join([app_format.format(app) for app in self.apps])
        
        self._render_template(
            'project_template/core/settings/base.py',
            settings_dir / 'base.py',
            {
                'parent_dir': parent_dir,
                'apps_imports': apps_imports,
                'core_path': self.core_path,
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
                f'project_template/core/settings/{env}.py',
                settings_dir / f'{env}.py',
                {
                    'core_path': self.core_path,
                    'static_media_settings': static_media_settings
                }
            )
        
        # Initalize settings module with proper environment
        self._render_template(
            'project_template/core/settings/__init__.py',
            settings_dir / '__init__.py',
            {'env': self.env}
        )

    def _generate_apps(self) -> None:
        """Generate all specified apps"""
        for app in self.apps:
            app_dir = self.project_path / Config.DEFAULT_PROJECT_STRUCTURE['apps_dir'] / app
            app_dir.mkdir(exist_ok=True)

            for file in Config.DEFAULT_FILES['app']:
                self._render_template(
                    f'app_template/{file}.template',
                    app_dir / file,
                    {'app_name': app}
                )

            (app_dir / 'migrations').mkdir(exist_ok=True)
            (app_dir / 'tests').mkdir(exist_ok=True)

            self._render_template(
                'app_template/tests/test_models.py.template',
                app_dir / 'tests' / 'test_models.py'
            )

            self._render_template(
                'app_template/migrations/__init__.py.template',
                app_dir / 'migrations' / '__init__.py'
            )

    def _render_template(self, template_name: str, output_path: Path, context: Optional[Dict] = None) -> None:
        """Render a template file with the given context"""
        context = context or {}
        template_ext = Config.TEMPLATE_CONFIG['template_ext']

        template_full_path = Path(Config.TEMPLATE_CONFIG['template_dir']) / template_name
        if not template_full_path.exists():
            if not template_name.endswith(template_ext):
                template_name += template_ext
                template_full_path = Path(Config.TEMPLATE_CONFIG['template_dir']) / template_name
            
            if not template_full_path.exists():
                raise FileNotFoundError(
                    f"Template '{template_name}' not found in: {template_full_path.parent}"
                )
        
        if Config.TEMPLATE_CONFIG['template_engine'] == 'jinja2':
            from jinja2 import Environment, FileSystemLoader
            template_dir = template_full_path.parent
            template_file = template_full_path.name
            env = Environment(loader=FileSystemLoader(template_dir))
            template = env.get_template(template_file)
            rendered = template.render(**context)
        # else:
        #     from string import Template
        #     with open(template_full_path) as f:
        #         template = Template(f.read())
        #     rendered = template.safe_substitute(**context)  #  safe_substitute to avoid errors for missing placeholders

        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(rendered)

def main():
    parser = argparse.ArgumentParser(
        description='Django Project Boilerplate Generator',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        'project_name',
        help='Name of the Django project'
    )

    parser.add_argument(
        '--apps',
        nargs='+',
        default=Config.CLI_DEFAULTS['apps'],
        help='List of apps to create'
    )
    
    parser.add_argument(
        '--core-location',
        choices=['inside', 'outside'],
        default=Config.DEFAULT_PROJECT_STRUCTURE['core_location'],
        help='Location of core configuration'
    )
    
    parser.add_argument(
        '--docker',
        action='store_true',
        default=Config.CLI_DEFAULTS['use_docker'],
        help='Include Docker configuration'
    )
    
    parser.add_argument(
        '--celery',
        action='store_true',
        default=Config.CLI_DEFAULTS['use_celery'],
        help='Include Celery configuration'
    )
    
    parser.add_argument(
        '--redis',
        action='store_true',
        default=Config.CLI_DEFAULTS['use_redis'],
        help='Include Redis configuration'
    )
    
    parser.add_argument(
        '--env',
        choices=['dev', 'prod'],
        default='dev',
        help='Environment to configure'
    )
    
    args = parser.parse_args()
    
    try:
        generator = DjangoBoilerplateGenerator(
            project_name=args.project_name,
            apps=args.apps,
            core_location=args.core_location,
            use_docker=args.docker,
            use_celery=args.celery,
            use_redis=args.redis,
            env=args.env
        )
        print("Generating project...")
        generator.generate_project()
    except (InvalidProjectNameError, InvalidAppNameError) as e:
        print(f"Error: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)

if __name__ == '__main__':
    main()