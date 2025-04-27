from typing import Any, Dict

from core.configuration_manager import (
    ConfigurationManager,
)
from core.project_structure_manager import ProjectStructureManager

from ..file_renderer import (
    FileRenderer,
)
from ..requirements_manager import (
    RequirementsManager,
)
from .base import BaseServiceGenerator

class CeleryGenerator(BaseServiceGenerator):
    """
    Generates configuration files and code snippets for integrating Celery.
    """
    service_name = "celery"
    def __init__(self, structure_manager: ProjectStructureManager, file_renderer: FileRenderer, requirements_manager: RequirementsManager, options: Dict[str, Any]):
        """
        Initialize the CeleryGenerator.

        Args:
            structure_manager: The ProjectStructureManager instance.
            file_renderer: The FileRenderer instance for rendering templates.
            requirements_manager: The RequirementsManager instance for managing dependencies. # Added requirements_manager
            options: Service-specific options for Celery (e.g., broker).
        """
        self.structure_manager = structure_manager
        self.file_renderer = file_renderer
        self.requirements_manager = requirements_manager # Store the requirements manager
        self.project_path = structure_manager.project_path
        self.options = options or {} # Ensure options is a dictionary

        # Base directory for Celery templates
        # Assuming Celery templates are in a 'celery_template' subdirectory within the main template directory
        self.template_base_dir = 'celery_template'

        # Get default options using the Config method
        celery_defaults = ConfigurationManager.get_service_default_options('celery') # Correctly access default options

        # Get options with defaults, prioritizing user-provided options
        self.broker = self.options.get('broker', celery_defaults.get('broker', 'redis')) # Corrected access
        self.use_flower = self.options.get('use_flower', celery_defaults.get('use_flower', False)) # Corrected access


    def generate(self) -> None:
        """
        Generates all Celery-related files and updates necessary project files.
        """
        # Generate the main celery.py file in the core project directory
        self._generate_celery_app_file()

        # Update the core project's __init__.py to include the Celery app
        self._update_core_init()

        # Update settings files with Celery configuration
        self._update_settings_files()

        # Add required packages to requirements.txt using the RequirementsManager
        self._add_required_packages()

    def _generate_celery_app_file(self) -> None:
        """
        Generates the celery.py file in the core project directory.
        """
        core_path = self.structure_manager.get_core_path()
        template_name = f'{self.template_base_dir}/celery.py.template'
        output_path = core_path / 'celery.py' # Place celery.py in the core directory

        # Determine the correct import path for the core settings module
        core_import_base = str(self.structure_manager.structure['core']['path']).replace('/', '.')

        context = {
            'project_name': self.structure_manager.project_name,
            'core_import_base': core_import_base,
            # Add other context variables needed for celery.py template
        }

        self.file_renderer.render_template(template_name, output_path, context)

    def _update_core_init(self) -> None:
        """
        Updates the core project's __init__.py file to include the Celery app import.
        """
        core_path = self.structure_manager.get_core_path()
        init_path = core_path / '__init__.py'

        # Determine the correct import statement based on core location
        core_import_base = str(self.structure_manager.structure['core']['path']).replace('/', '.')
        # Use relative import if core is not at the root
        if core_import_base == 'core': # Assuming 'core' is the default root path
             celery_import_statement = "from .celery import app as celery_app"
        else:
             celery_import_statement = f"from .{core_import_base}.celery import app as celery_app"


        # Content to add to __init__.py
        # Ensure a newline before adding the content if the file is not empty and doesn't end with one
        celery_init_content_to_add = f"""
# Import Celery app
{celery_import_statement}

# Define __all__ to explicitly export celery_app (optional but good practice)
try:
    __all__ = ('celery_app',)
except NameError:
    # This might happen if celery_app is not defined (e.g., in a test environment)
    pass
""" # Added a try/except for __all__ for robustness


        # Read existing content
        existing_content = ""
        if init_path.exists():
            with open(init_path, 'r', encoding='utf-8') as f: # Specify encoding
                existing_content = f.read()

        # Only append if the import statement is not already present
        if celery_import_statement not in existing_content:
            with open(init_path, 'a', encoding='utf-8') as f: # Specify encoding
                # Add a newline before appending if the file doesn't end with one
                if existing_content and not existing_content.endswith('\n'):
                     f.write('\n')
                f.write(celery_init_content_to_add)


    def _update_settings_files(self) -> None:
        """
        Updates the settings files (specifically base.py) with Celery configuration.
        """
        core_path = self.structure_manager.get_core_path()
        settings_path = core_path / 'settings' / 'base.py'

        if not settings_path.exists():
            print(f"Warning: base.py not found at {settings_path}. Cannot add Celery settings.") # Or raise an error
            return

        # Determine broker URL based on the selected broker option
        if self.broker == 'redis':
             broker_url = "redis://redis:6379/0"
        elif self.broker == 'rabbitmq':
             broker_url = "amqp://guest:guest@rabbitmq:5672//"
        else:
             # Default or handle other brokers
             broker_url = "redis://redis:6379/0" # Fallback to redis


        celery_settings = f"""

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', '{broker_url}')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', '{broker_url}')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
# Add other Celery settings as needed (e.g., CELERY_BEAT_SCHEDULE)
"""
        # Need to add 'os' import if not already present in base.py template
        # This could be handled more robustly by checking imports in the file or
        # by ensuring the base.py template always includes necessary standard imports.

        # Read existing content
        existing_content = ""
        with open(settings_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        # Only append if Celery settings are not already present
        if 'CELERY_BROKER_URL' not in existing_content:
             # Add os import if not present and not already added by another service
            if 'import os' not in existing_content:
                 existing_content = 'import os\n' + existing_content
                 # Add a newline if the file didn't start with one after adding import
                 if not existing_content.startswith('\n'):
                     existing_content = '\n' + existing_content

            with open(settings_path, 'w', encoding='utf-8') as f: # Specify encoding
                f.write(existing_content + celery_settings)


    def _add_required_packages(self) -> None:
        """
        Adds required Python packages for Celery to requirements.txt using RequirementsManager.
        """
        required_packages = [
            'celery>=5.2.0',
            'django-celery-results>=2.4.0',
        ]

        # Add broker-specific packages based on the selected broker option
        if self.broker == 'redis': # Use self.broker
             required_packages.append('redis>=4.0.0')
        elif self.broker == 'rabbitmq': # Use self.broker
             required_packages.append('kombu>=5.2.0')

        # Add flower if option is selected
        if self.use_flower: # Use self.use_flower
             required_packages.append('flower>=1.0.0')


        # Use the RequirementsManager to add the packages
        self.requirements_manager.add_packages(required_packages)
