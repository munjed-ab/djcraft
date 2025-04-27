from pathlib import Path

from core.config import DefaultSettings
from core.project_structure_manager import ProjectStructureManager

from .abstract_generator import AbstractGenerator
from .file_renderer import FileRenderer
from .requirements_manager import RequirementsManager


class CoreFileGenerator(AbstractGenerator):
    """
    Generates the core Django project files (settings, urls, wsgi, asgi) using Template Method pattern.
    """
    def __init__(self, structure_manager: ProjectStructureManager, 
                 file_renderer: FileRenderer,
                 requirements_manager: RequirementsManager,
                 config = None):
        """
        Initialize the CoreFileGenerator.

        Args:
            structure_manager: The ProjectStructureManager instance.
            file_renderer: The FileRenderer instance for rendering templates.
            requirements_manager: The RequirementsManager instance.
            config: Optional configuration dictionary.
        """
        super().__init__(structure_manager, file_renderer, requirements_manager, config)
        self.core_path = structure_manager.get_core_path()
        self.template_base_dir = 'project_template/core'


    def create_directories(self) -> None:
        """
        Create necessary directories for core files.
        """
        self.core_path.mkdir(parents=True, exist_ok=True)
        settings_dir = self.core_path / 'settings'
        settings_dir.mkdir(exist_ok=True)
        
    def generate_files(self) -> None:
        """
        Generate all core Django files.
        """
        self._generate_main_core_files()
        self._generate_settings_files()

    def _generate_main_core_files(self) -> None:
        """
        Generates the primary files within the core project directory.
        """
        core_import_base = str(self.structure_manager.structure['core']['path']).replace('/', '.')

        app_import_paths = self.structure_manager.get_python_import_paths()
        included_services = [s['name'] for s in self.structure_manager.structure['services'] or []]
        context_urls = {
            'project_name': self.project_name,
            'core_import_base': core_import_base,
            'use_rest_api': 'rest_api' in included_services,
            'use_auth': 'authentication' in included_services,
            'apps': app_import_paths.items()
        }
        self.file_renderer.render_template(
            f'{self.template_base_dir}/urls.py.template',
            self.core_path / 'urls.py',
            context_urls
        )

        context_wsgi = {
            'core_import_base': core_import_base
        }
        self.file_renderer.render_template(
            f'{self.template_base_dir}/wsgi.py.template',
            self.core_path / 'wsgi.py',
            context_wsgi
        )

        context_asgi = {
            'core_import_base': core_import_base
        }
        self.file_renderer.render_template(
            f'{self.template_base_dir}/asgi.py.template',
            self.core_path / 'asgi.py',
            context_asgi
        )

        # Generate core __init__.py
        # This might need to include imports for services like Celery if they are added
        included_services = [s['name'] for s in self.structure_manager.structure.get('services', [])] # Re-get included services
        context_core_init = {
            'use_celery': 'celery' in included_services
        }
        self.file_renderer.render_template(
            f'{self.template_base_dir}/__init__.py.template',
            self.core_path / '__init__.py',
            context_core_init
        )


    def _generate_settings_files(self) -> None:
        """
        Generates the settings files within the core project's settings directory.
        """
        settings_dir = self.core_path / 'settings'
        settings_dir.mkdir(exist_ok=True)

        # Get Python import paths for installed apps
        app_import_paths = self.structure_manager.get_python_import_paths()

        # Get default Django apps from ConfigurationManager
        default_django_apps = DefaultSettings.DJANGO_DEFAULTS.default_apps or []

        # Combine default Django apps and project apps (pass as a list)
        all_installed_apps_list = default_django_apps + list(app_import_paths.values())

        # Get default middleware from ConfigurationManager (pass as a list)
        default_middleware_list = DefaultSettings.DJANGO_DEFAULTS.default_middleware or []

        # Determine the correct BASE_DIR calculation based on core location
        core_path_parts = Path(self.structure_manager.structure['core']['path']).parts
        core_depth = len(core_path_parts)
        num_parents = core_depth + 1 # +1 for the settings directory itself
        parent_dir_calculation = ".parent" * num_parents


        included_services = [s['name'] for s in self.structure_manager.structure.get('services', [])]
        context_settings = {
            'project_name': self.project_name,
            'installed_apps_list': all_installed_apps_list,
            'middleware_list': default_middleware_list,
            'parent_dir_calculation': parent_dir_calculation,
            'core_import_base': str(self.structure_manager.structure['core']['path']).replace('/', '.'),
            'use_rest_api': 'rest_api' in included_services,
            'use_redis': 'redis' in included_services,
            'use_celery': 'celery' in included_services,
            'use_auth': 'authentication' in included_services,
            'use_db_router': 'db_router' in included_services,
            'env': self.structure_manager.structure.get('env', 'dev'),
            'django_version': '4.0',
            'secret_key_placeholder': 'changeme'
        }

        self.file_renderer.render_template(
            f'{self.template_base_dir}/settings/base.py.template',
            settings_dir / 'base.py',
            context_settings
        )

        # Generate environment-specific settings files (dev.py, prod.py)
        # These templates will likely import from base.py
        for env in ['dev', 'prod']:
            self.file_renderer.render_template(
                f'{self.template_base_dir}/settings/{env}.py.template',
                settings_dir / f'{env}.py',
                context_settings # Pass the same context, templates can filter what they need
            )

        # This file typically imports settings based on an environment variable
        self.file_renderer.render_template(
            f'{self.template_base_dir}/settings/__init__.py.template',
            settings_dir / '__init__.py',
            context_settings # Pass context, template needs 'env'
        )

