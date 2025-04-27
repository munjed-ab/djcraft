from typing import Any, Dict

from core.configuration_manager import ConfigurationManager
from core.project_structure_manager import ProjectStructureManager

from ..file_renderer import FileRenderer
from ..requirements_manager import RequirementsManager
from .base import BaseServiceGenerator

class DbRouterGenerator(BaseServiceGenerator):
    """
    Generates a database router for handling multiple databases or specific app routing.
    """
    service_name = "db-router"
    def __init__(self, structure_manager: ProjectStructureManager, file_renderer: FileRenderer, requirements_manager: RequirementsManager, options: Dict[str, Any]):
        """
        Initialize the DbRouterGenerator.

        Args:
            structure_manager: The ProjectStructureManager instance.
            file_renderer: The FileRenderer instance.
            requirements_manager: The RequirementsManager instance.
            options: Service-specific options for the database router (e.g., app_routing_map).
        """
        self.structure_manager = structure_manager
        self.file_renderer = file_renderer
        self.requirements_manager = requirements_manager
        self.project_path = structure_manager.project_path
        self.options = options or {}

        # Assuming DB Router templates are in a 'db_router_template' subdirectory
        self.template_base_dir = 'db_template'

        # Get default options using the DefaultSettings method
        db_router_defaults = ConfigurationManager.get_service_default_options('db_router') # Correctly access default options

        # Get options with defaults, prioritizing user-provided options
        # Example option: a dictionary mapping app names to database aliases
        self.app_routing_map = self.options.get('app_routing_map', db_router_defaults.get('app_routing_map', {}))
        self.db_types = self.options.get('db_types', db_router_defaults.get('db_types', ['postgres'])) # Example option


    def generate(self) -> None:
        """
        Generates the database router file and updates settings.
        """
        # Generate the database router file
        self._generate_router_file()

        # Update settings files to use the database router
        self._update_settings_files()

        # Add required packages (usually none specific to a basic router)
        self._add_required_packages()

    def _generate_router_file(self) -> None:
        """
        Generates the database router Python file.
        """
        core_path = self.structure_manager.get_core_path()
        template_name = f'{self.template_base_dir}/router.py.template' # Assuming this template exists
        output_path = core_path / 'router.py' # Place router.py in the core directory

        # Prepare context data for the router template
        context = {
            'app_routing_map': self.app_routing_map,
            # You might need to pass a list of all app names here too
            'all_apps': list(self.structure_manager.structure['apps'].keys()),
            'db_types': self.db_types # Pass db types to template
        }

        self.file_renderer.render_template(template_name, output_path, context)


    def _update_settings_files(self) -> None:
        """
        Updates the settings files (specifically base.py) to include the DATABASE_ROUTERS setting.
        """
        core_path = self.structure_manager.get_core_path()
        settings_path = core_path / 'settings' / 'base.py'

        if not settings_path.exists():
            print(f"Warning: base.py not found at {settings_path}. Cannot configure database router.")
            return

        # Determine the correct import path for the core router module
        core_import_base = str(self.structure_manager.structure['core']['path']).replace('/', '.')
        router_import_path = f'{core_import_base}.router.DatabaseRouter' # Assuming the router class is named DatabaseRouter

        db_router_setting = f"""

# Database Router Configuration
DATABASE_ROUTERS = ['{router_import_path}']
"""
        # Read existing content
        existing_content = ""
        with open(settings_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        # Only append if DATABASE_ROUTERS setting is not already present
        if 'DATABASE_ROUTERS' not in existing_content:
            with open(settings_path, 'w', encoding='utf-8') as f:
                f.write(existing_content + db_router_setting)

        # You might also need to add DATABASE settings for the different databases
        # This would involve reading the existing DATABASES setting and adding new entries
        # based on the app_routing_map and db_types. This is complex string manipulation
        # and better handled with a more sophisticated settings update mechanism or template logic.
        print("Reminder: Manually configure DATABASE settings for your database router in settings.")


    def _add_required_packages(self) -> None:
        """
        Adds required Python packages for the database router to requirements.txt.
        (Usually none specific to a basic router).
        """
        required_packages = [
            # Add packages here if needed for specific router implementations (e.g., database drivers)
        ]
        # Add database driver packages based on selected db_types
        if 'postgres' in self.db_types:
             required_packages.append('psycopg2-binary')
        if 'mysql' in self.db_types:
             required_packages.append('mysqlclient')
        # Sqlite is built-in
        if required_packages:
             self.requirements_manager.add_packages(required_packages)

