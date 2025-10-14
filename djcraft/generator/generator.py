from pathlib import Path
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from core.configuration_manager import ConfigurationManager
from core.project_structure_manager import ProjectStructureManager
from .file_renderer import FileRenderer
from .requirements_manager import RequirementsManager


# ============================================================================
# BASE GENERATOR
# ============================================================================

class BaseGenerator(ABC):
    """
    Simple base class for all generators.
    Only handles common initialization, no complex template method.
    """
    
    def __init__(
        self,
        structure_manager: ProjectStructureManager,
        file_renderer: FileRenderer,
        requirements_manager: RequirementsManager,
        config: Optional[ConfigurationManager] = None
    ):
        self.structure_manager = structure_manager
        self.file_renderer = file_renderer
        self.requirements_manager = requirements_manager
        self.config = config or ConfigurationManager()
        
        self.project_path = structure_manager.project_path
        self.project_name = structure_manager.project_name
    
    @abstractmethod
    def generate(self) -> None:
        """Generate files. Each generator implements its own logic."""
        pass
    
    def get_base_context(self) -> Dict[str, Any]:
        """Common context for all templates."""
        return {
            'project_name': self.project_name,
            'project_path': str(self.project_path)
        }


# ============================================================================
# BASE PROJECT FILES GENERATOR
# ============================================================================

class BaseProjectFilesGenerator(BaseGenerator):
    """Generates base project files: manage.py, .gitignore, README.md"""
    
    def generate(self) -> None:
        """Generate all base project files."""
        self._generate_manage_py()
        self._generate_gitignore()
        self._generate_readme()
    
    def _generate_manage_py(self) -> None:
        core_path = self.structure_manager.get_core_path_str().replace('/', '.')
        context = {**self.get_base_context(), 'core_path': core_path}
        
        output_path = self.project_path / 'manage.py'
        self.file_renderer.render_template(
            'project_template/manage.py.template',
            output_path,
            context
        )
        output_path.chmod(0o755)  #  executable
    
    def _generate_gitignore(self) -> None:
        self.file_renderer.render_template(
            'project_template/.gitignore.template',
            self.project_path / '.gitignore',
            self.get_base_context()
        )
    
    def _generate_readme(self) -> None:
        services = [s['name'] for s in self.structure_manager.get_services()]
        context = {
            **self.get_base_context(),
            'apps': list(self.structure_manager.structure['apps'].keys()),
            'use_docker': 'docker' in services,
            'use_celery': 'celery' in services,
            'use_rest_api': 'rest_api' in services,
        }
        self.file_renderer.render_template(
            'project_template/README.md.template',
            self.project_path / 'README.md',
            context
        )


# ============================================================================
# CORE FILES GENERATOR
# ============================================================================

class CoreFileGenerator(BaseGenerator):
    """Generates Django core files: settings, urls, wsgi, asgi"""
    
    def generate(self) -> None:
        """Generate all core Django files."""
        core_path = self.structure_manager.get_core_path()
        core_path.mkdir(parents=True, exist_ok=True)
        
        self._generate_core_init()
        self._generate_urls()
        self._generate_wsgi()
        self._generate_asgi()
        self._generate_settings()
    
    def _get_core_context(self) -> Dict[str, Any]:
        """Get context for core file templates"""
        core_import_path = self.structure_manager.get_core_path_str().replace('/', '.')
        services = [s['name'] for s in self.structure_manager.get_services()]
        
        return {
            **self.get_base_context(),
            'core_import_path': core_import_path,
            'apps': self.structure_manager.get_python_import_paths(),
            'use_celery': 'celery' in services,
            'use_rest_api': 'rest_api' in services,
            'use_redis': 'redis' in services,
        }
    
    def _generate_core_init(self) -> None:
        core_path = self.structure_manager.get_core_path()
        self.file_renderer.render_template(
            'project_template/core/__init__.py.template',
            core_path / '__init__.py',
            self._get_core_context()
        )
    
    def _generate_urls(self) -> None:
        core_path = self.structure_manager.get_core_path()
        self.file_renderer.render_template(
            'project_template/core/urls.py.template',
            core_path / 'urls.py',
            self._get_core_context()
        )
    
    def _generate_wsgi(self) -> None:
        core_path = self.structure_manager.get_core_path()
        self.file_renderer.render_template(
            'project_template/core/wsgi.py.template',
            core_path / 'wsgi.py',
            self._get_core_context()
        )
    
    def _generate_asgi(self) -> None:
        core_path = self.structure_manager.get_core_path()
        self.file_renderer.render_template(
            'project_template/core/asgi.py.template',
            core_path / 'asgi.py',
            self._get_core_context()
        )
    
    def _generate_settings(self) -> None:
        """Generate settings directory with base, dev, prod settings"""
        core_path = self.structure_manager.get_core_path()
        settings_dir = core_path / 'settings'
        settings_dir.mkdir(exist_ok=True)
        
        # calculateng BASE_DIR parent count
        core_depth = len(Path(self.structure_manager.get_core_path_str()).parts)
        parent_calculation = ".parent" * (core_depth + 1)
        
        context = {
            **self._get_core_context(),
            'parent_dir_calculation': parent_calculation,
            'installed_apps': self._get_installed_apps(),
            'middleware': self._get_middleware(),
        }
        
        for filename in ['base.py', 'dev.py', 'prod.py', '__init__.py']:
            self.file_renderer.render_template(
                f'project_template/core/settings/{filename}.template',
                settings_dir / filename,
                context
            )
    
    def _get_installed_apps(self) -> List[str]:
        config_dict = self.config.get_all_config()
        default_apps = config_dict['django']['default_apps']
        project_apps = list(self.structure_manager.get_python_import_paths().values())
        return default_apps + project_apps
    
    def _get_middleware(self) -> List[str]:
        config_dict = self.config.get_all_config()
        return config_dict['django']['default_middleware']


# ============================================================================
# APP GENERATOR
# ============================================================================

class AppGenerator(BaseGenerator):
    """Generates Django apps with different types (standard, api, auth)."""
    
    APP_TYPE_FILES = {
        'standard': ['__init__.py', 'admin.py', 'apps.py', 'models.py', 'views.py', 'urls.py'],
        'api': ['__init__.py', 'admin.py', 'apps.py', 'models.py', 'views.py', 'urls.py', 'serializers.py'],
        'auth': ['__init__.py', 'admin.py', 'apps.py', 'models.py', 'views.py', 'urls.py', 'forms.py'],
    }
    
    def generate(self) -> None:
        apps = self.structure_manager.structure.get('apps', {})
        
        if not apps:
            print("No apps to generate")
            return
        
        for app_name, app_path_str in apps.items():
            self._generate_app(app_name, app_path_str)
    
    def _generate_app(self, app_name: str, app_path_str: str) -> None:
        """Generate a single Django app"""
        print(f"Generating app: {app_name}")
        
        # Create app directory
        app_dir = self.project_path / app_path_str
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Git app type
        app_type = self._get_app_type(app_name)
        print(f"  Type: {app_type}")
        
        # Generate app files
        self._generate_app_files(app_name, app_dir, app_path_str, app_type)
        
        # Generate subdirectories
        self._generate_migrations_dir(app_dir)
        self._generate_tests_dir(app_dir, app_name)
        
        print(f"Generated the app {app_name} successfully..")
    
    def _get_app_type(self, app_name: str) -> str:
        """Determine app type from name or configuration."""
        #  rules - TODO: extended it via config later
        if 'api' in app_name.lower():
            return 'api'
        elif app_name in ['users', 'accounts', 'auth', 'authentication']:
            return 'auth'
        return 'standard'
    
    def _generate_app_files(
        self,
        app_name: str,
        app_dir: Path,
        app_path_str: str,
        app_type: str
    ) -> None:
        """Generate all files for an app based on its type"""
        app_import_path = app_path_str.replace('/', '.')
        
        # Get files 
        files = self.APP_TYPE_FILES.get(app_type, self.APP_TYPE_FILES['standard'])
        
        context = {
            'app_name': app_name,
            'app_import_path': app_import_path,
        }
        
        # Generate each file
        for filename in files:
            template_name = f'app_template/{filename}.template'
            output_path = app_dir / filename
            
            try:
                self.file_renderer.render_template(template_name, output_path, context)
                print(f"    Good {filename}")
            except Exception as e:
                print(f"    Error {filename}: {e}")
    
    def _generate_migrations_dir(self, app_dir: Path) -> None:
        migrations_dir = app_dir / 'migrations'
        migrations_dir.mkdir(exist_ok=True)
        (migrations_dir / '__init__.py').touch()
    
    def _generate_tests_dir(self, app_dir: Path, app_name: str) -> None:
        tests_dir = app_dir / 'tests'
        tests_dir.mkdir(exist_ok=True)
        
        (tests_dir / '__init__.py').touch()
        
        context = {'app_name': app_name}
        self.file_renderer.render_template(
            'app_template/tests/test_models.py.template',
            tests_dir / 'test_models.py',
            context
        )


# ============================================================================
# SERVICE GENERATOR 
# ============================================================================

class ServiceGenerator(BaseGenerator):
    """Generates service configurations (Docker, Celery, Redis, etc.)"""
    
    def generate(self) -> None:
        services = self.structure_manager.structure.get('services', [])
        
        for service_config in services:
            service_name = service_config.get('name')
            if not service_name:
                continue
            
            method_name = f'_generate_{service_name}'
            if hasattr(self, method_name):
                print(f"Generating service: {service_name}")
                method = getattr(self, method_name)
                method(service_config.get('options', {}))
            else:
                print(f"Warning: No generator for service '{service_name}'")
    
    def _generate_docker(self, options: Dict[str, Any]) -> None:
        context = {
            **self.get_base_context(),
            'python_version': options.get('python_version', '3.9'),
            'postgres_version': options.get('postgres_version', '13'),
        }
        
        self.file_renderer.render_template(
            'services/docker/Dockerfile.template',
            self.project_path / 'Dockerfile',
            context
        )
        
        self.file_renderer.render_template(
            'services/docker/docker-compose.yml.template',
            self.project_path / 'docker-compose.yml',
            context
        )
        
        self.requirements_manager.add_packages(['gunicorn', 'psycopg2-binary'])
    
    def _generate_celery(self, options: Dict[str, Any]) -> None:
        core_path = self.structure_manager.get_core_path()
        
        context = {
            **self.get_base_context(),
            'core_import_path': self.structure_manager.get_core_path_str().replace('/', '.'),
            'broker': options.get('broker', 'redis'),
        }
        
        self.file_renderer.render_template(
            'services/celery/celery.py.template',
            core_path / 'celery.py',
            context
        )
        
        self.requirements_manager.add_packages(['celery', 'redis'])
    
    def _generate_redis(self, options: Dict[str, Any]) -> None:
        # Redis config goes in settings, no separate file needed
        self.requirements_manager.add_packages(['redis', 'django-redis'])
    
    def _generate_rest_api(self, options: Dict[str, Any]) -> None:
        self.requirements_manager.add_packages(['djangorestframework'])


# ============================================================================
# MAIN PROJECT GENERATOR 
# ============================================================================

class DjangoProjectGenerator:
    """
    Main generator that manage/uses all sub-generators
    """
    
    def __init__(
        self,
        structure_manager: ProjectStructureManager,
        config: Optional[ConfigurationManager] = None
    ):
        self.structure_manager = structure_manager
        self.config = config or ConfigurationManager()
        
        self.file_renderer = FileRenderer("templates")
        self.requirements_manager = RequirementsManager(structure_manager.project_path)
        
        self.generators = {
            'base_files': BaseProjectFilesGenerator(
                structure_manager, self.file_renderer, self.requirements_manager, self.config
            ),
            'core_files': CoreFileGenerator(
                structure_manager, self.file_renderer, self.requirements_manager, self.config
            ),
            'apps': AppGenerator(
                structure_manager, self.file_renderer, self.requirements_manager, self.config
            ),
            'services': ServiceGenerator(
                structure_manager, self.file_renderer, self.requirements_manager, self.config
            ),
        }
    
    def generate(self) -> None:
        print(f"\nGenerating Django project '{self.structure_manager.project_name}'")
        print(f"Location: {self.structure_manager.project_path}")
       
        # main project dir
        self.structure_manager.project_path.mkdir(parents=True, exist_ok=True)
        
        for name, generator in self.generators.items():
            print(f"\n[{name.upper()}]")
            try:
                generator.generate()
            except Exception as e:
                print(f"Error in {name}: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n[REQUIREMENTS]")
        self.requirements_manager.write_requirements_file()
        print("    requirements.txt")
        
        print("Project generation complete!\n")

