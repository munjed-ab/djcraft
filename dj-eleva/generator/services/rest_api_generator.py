from typing import Any, Dict

from core.configuration_manager import ConfigurationManager
from core.project_structure_manager import ProjectStructureManager

from ..file_renderer import FileRenderer
from ..requirements_manager import RequirementsManager
from .base import BaseServiceGenerator


class RestAPIGenerator(BaseServiceGenerator):
    """
    Generates configuration and updates settings for integrating a REST API framework (like DRF).
    """
    service_name = "rest-api"
    def __init__(self, structure_manager: ProjectStructureManager, file_renderer: FileRenderer, requirements_manager: RequirementsManager, options: Dict[str, Any]):
        """
        Initialize the RestAPIGenerator.

        Args:
            structure_manager: The ProjectStructureManager instance.
            file_renderer: The FileRenderer instance.
            requirements_manager: The RequirementsManager instance.
            options: Service-specific options for REST API.
        """
        self.structure_manager = structure_manager
        self.file_renderer = file_renderer
        self.requirements_manager = requirements_manager
        self.project_path = structure_manager.project_path
        self.options = options or {}

        # Assuming REST API templates are in a 'rest_api_template' subdirectory
        self.template_base_dir = 'rest_api_template'
        rest_api_defaults = ConfigurationManager.get_service_default_options('rest_api')
        # Get options with defaults
        self.framework = self.options.get('framework', rest_api_defaults.get('framework', 'drf'))


    def generate(self) -> None:
        """
        Generates REST API-related configurations and updates.
        """
        if self.framework == 'drf':
            self._configure_drf()
        # Add logic for other frameworks here if needed

        # Add required packages for the chosen framework
        self._add_required_packages()

    def _configure_drf(self) -> None:
        """
        Configures Django Rest Framework (DRF).
        Updates settings and potentially adds a root API URL file.
        """
        # Update settings files with DRF configuration
        self._update_settings_files_for_drf()

        # Generate a root api_urls.py file if needed
        self._generate_root_api_urls()


    def _update_settings_files_for_drf(self) -> None:
        """
        Updates the settings files (specifically base.py) with DRF configuration.
        """
        core_path = self.structure_manager.get_core_path()
        settings_path = core_path / 'settings' / 'base.py'

        if not settings_path.exists():
            print(f"Warning: base.py not found at {settings_path}. Cannot configure DRF.")
            return

        drf_settings = """

# Django Rest Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    # Add other DRF settings as needed (e.g., pagination, throttling)
}

# Optional: Add settings for authentication methods if they are included as services
# if 'authentication' in [s['name'] for s in INSTALLED_APPS]: # Example check
#    REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].append('path.to.YourAuthBackend')

"""
        # Need to add 'rest_framework' to INSTALLED_APPS in base.py
        # This could be done by reading and modifying the INSTALLED_APPS list in base.py
        # or by having a more sophisticated settings update mechanism.
        # For simplicity here, we'll assume INSTALLED_APPS is a variable we can append to
        # in the base.py template, or we'll rely on the CoreFileGenerator to handle this
        # based on the services included. A better approach is needed here.

        # For now, let's just append the settings block.
        # A more robust solution would involve parsing/modifying the INSTALLED_APPS list.

        # Read existing content
        existing_content = ""
        with open(settings_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        # Only append if REST_FRAMEWORK settings are not already present
        if 'REST_FRAMEWORK' not in existing_content:
            with open(settings_path, 'w', encoding='utf-8') as f:
                f.write(existing_content + drf_settings)

        # --- Need a better way to add to INSTALLED_APPS ---
        # This is a limitation of simply appending strings.
        # A more advanced approach would involve:
        # 1. Reading the base.py file.
        # 2. Parsing the AST or using regex to find the INSTALLED_APPS list.
        # 3. Appending 'rest_framework' to the list.
        # 4. Writing the modified content back.
        # Or, modify the base.py template to dynamically include app/service names in INSTALLED_APPS.
        print("Warning: Manually add 'rest_framework' to INSTALLED_APPS in your settings.") # Temporary warning


    def _generate_root_api_urls(self) -> None:
        """
        Generates a root api_urls.py file in the core project directory.
        This file is typically included in the main urls.py.
        """
        core_path = self.structure_manager.get_core_path()
        template_name = f'{self.template_base_dir}/api_urls.py.template' # Assuming this template exists
        output_path = core_path / 'api_urls.py'

        # Determine the correct import path for the core settings module
        core_import_base = str(self.structure_manager.structure['core']['path']).replace('/', '.')

        context = {
            'core_import_base': core_import_base,
            # Add context for included services that might need API endpoints (e.g., Auth)
            'use_auth': 'authentication' in [s['name'] for s in self.structure_manager.structure.get('services', [])]
        }

        self.file_renderer.render_template(template_name, output_path, context)

        # Note: You will need to manually include this api_urls.py in your main urls.py
        # This could potentially be automated by modifying the main urls.py template
        # in the CoreFileGenerator based on included services.


    def _add_required_packages(self) -> None:
        """
        Adds required Python packages for the chosen REST API framework to requirements.txt.
        """
        required_packages = []
        if self.framework == 'drf':
            required_packages.append('djangorestframework>=3.12.0')
            required_packages.append('djangorestframework-filters>=1.0.0') # Common dependency
            # Add packages for authentication methods if they are options (e.g., 'djangorestframework-simplejwt')
            if self.options.get('use_jwt'):
               required_packages.append('djangorestframework-simplejwt')


        if required_packages:
             self.requirements_manager.add_packages(required_packages)

