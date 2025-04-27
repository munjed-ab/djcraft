from typing import Any, Dict

from core.configuration_manager import ConfigurationManager
from core.project_structure_manager import ProjectStructureManager

from ..file_renderer import FileRenderer
from ..requirements_manager import RequirementsManager
from .base import BaseServiceGenerator


class AuthGenerator(BaseServiceGenerator):
    """
    Generates configuration and updates settings for enhanced authentication.
    This could include custom user models, authentication backends, etc.
    For this example, it will focus on setting up a basic custom user model.
    """
    service_name = "auth"
    def __init__(self, structure_manager: ProjectStructureManager, file_renderer: FileRenderer, requirements_manager: RequirementsManager, options: Dict[str, Any]):
        """
        Initialize the AuthGenerator.

        Args:
            structure_manager: The ProjectStructureManager instance.
            file_renderer: The FileRenderer instance.
            requirements_manager: The RequirementsManager instance.
            options: Service-specific options for Authentication.
        """
        self.structure_manager = structure_manager
        self.file_renderer = file_renderer
        self.requirements_manager = requirements_manager
        self.project_path = structure_manager.project_path
        self.options = options or {}

        # Assuming auth templates are in an 'auth_template' subdirectory
        self.template_base_dir = 'auth_template'

        # Get default options using the DefaultSettings method
        auth_defaults = ConfigurationManager.get_service_default_options('authentication')

        # Get options with defaults, prioritizing user-provided options
        self.use_custom_user = self.options.get('custom_user', auth_defaults.get('custom_user', True))
        self.custom_user_app_name = self.options.get('custom_user_app_name', auth_defaults.get('custom_user_app_name', 'users')) # Corrected access
        self.custom_user_app_directory = self.options.get('custom_user_app_directory', auth_defaults.get('custom_user_app_directory', '')) # Corrected access


    def generate(self) -> None:
        """
        Generates authentication-related configurations and updates.
        """
        if self.use_custom_user:
            # Generate the custom user model app (if not already created)
            self._generate_custom_user_app()

            # Update settings files to use the custom user model
            self._update_settings_files_for_custom_user()

            # Add required packages (if any specific to custom user model setup)
            self._add_required_packages()

        # Add other authentication related configurations here (e.g., social auth, JWT settings)
        # based on self.options and other services included.


    def _generate_custom_user_app(self) -> None:
        """
        Generates a dedicated app for the custom user model if 'custom_user' is true.
        Assumes a convention like 'users' app.
        """
        # Use instance variables for app name and directory
        custom_user_app_name = self.custom_user_app_name
        custom_user_app_dir = self.custom_user_app_directory

        # Check if the app already exists in the structure manager
        if custom_user_app_name not in self.structure_manager.structure['apps']:
            print(f"Generating custom user app: {custom_user_app_name}")
            try:
                # Add the app to the structure manager
                # Note: This modifies the structure_manager, which is used by AppGenerator.
                # Ensure AppGenerator is run AFTER AuthGenerator if it relies on this.
                # A better approach might be to add a flag/method to structure_manager
                # to indicate an app should be created by the main AppGenerator loop.
                self.structure_manager.add_app(custom_user_app_name, custom_user_app_dir)

                # Manually generate the app files here using the FileRenderer
                app_dir_path = self.project_path / (f"{custom_user_app_dir}/{custom_user_app_name}" if custom_user_app_dir else custom_user_app_name)
                app_dir_path.mkdir(parents=True, exist_ok=True)

                # Generate models.py with custom user model
                self.file_renderer.render_template(
                    f'{self.template_base_dir}/models.py.template',
                    app_dir_path / 'models.py',
                    {'app_name': custom_user_app_name} # Pass app name to template
                )

                # Generate admin.py for the custom user model
                self.file_renderer.render_template(
                    f'{self.template_base_dir}/admin.py.template',
                    app_dir_path / 'admin.py',
                     {'app_name': custom_user_app_name} # Pass app name to template
                )

                # Generate apps.py
                self.file_renderer.render_template(
                    f'{self.template_base_dir}/apps.py.template',
                    app_dir_path / 'apps.py',
                    {'app_name': custom_user_app_name} # Pass app name to template
                )

                 # Generate __init__.py
                self.file_renderer.render_template(
                    f'{self.template_base_dir}/__init__.py.template',
                    app_dir_path / '__init__.py'
                )

                # Generate migrations directory and __init__.py (basic)
                migrations_dir = app_dir_path / 'migrations'
                migrations_dir.mkdir(exist_ok=True)
                self.file_renderer.render_template(
                    f'{self.template_base_dir}/migrations/__init__.py.template',
                    migrations_dir / '__init__.py'
                )


            except Exception as e:
                print(f"Error generating custom user app '{custom_user_app_name}': {e}") # Or raise an error
        else:
            print(f"Custom user app '{custom_user_app_name}' already exists in structure.") # Or log info


    def _update_settings_files_for_custom_user(self) -> None:
        """
        Updates the settings files (specifically base.py) to point to the custom user model.
        """
        core_path = self.structure_manager.get_core_path()
        settings_path = core_path / 'settings' / 'base.py'

        if not settings_path.exists():
            print(f"Warning: base.py not found at {settings_path}. Cannot configure custom user model.")
            return

        # Use instance variable for app name
        custom_user_app_name = self.custom_user_app_name
        custom_user_model = f"{custom_user_app_name}.CustomUser" # Assuming CustomUser model name

        auth_user_model_setting = f"""

# Authentication Configuration
AUTH_USER_MODEL = '{custom_user_model}'
"""
        # Read existing content
        existing_content = ""
        with open(settings_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        # Only append if AUTH_USER_MODEL is not already present
        if 'AUTH_USER_MODEL' not in existing_content:
            with open(settings_path, 'w', encoding='utf-8') as f:
                f.write(existing_content + auth_user_model_setting)


    def _add_required_packages(self) -> None:
        """
        Adds required Python packages for authentication features to requirements.txt.
        (e.g., packages for social auth, JWT, etc., if implemented).
        For a basic custom user model, no extra packages might be needed beyond Django.
        """
        required_packages = [
            # Add packages here for specific auth features (e.g., 'django-allauth', 'djangorestframework-simplejwt')
        ]
        if required_packages:
             self.requirements_manager.add_packages(required_packages)

