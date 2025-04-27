from pathlib import Path
from typing import Any, Dict

from core.configuration_manager import (
    ConfigurationManager,
)
from core.project_structure_manager import ProjectStructureManager

from ..file_renderer import (
    FileRenderer,
)
from ..requirements_manager import RequirementsManager
from .base import BaseServiceGenerator


class DockerGenerator(BaseServiceGenerator): # Inherit from BaseServiceGenerator
    """
    Generates Docker-related configuration files (Dockerfile, docker-compose.yml, .dockerignore).
    """
    service_name = "docker"

    def __init__(self, structure_manager: ProjectStructureManager, file_renderer: FileRenderer, requirements_manager: RequirementsManager, options: Dict[str, Any]):
        """
        Initialize the DockerGenerator.

        Args:
            structure_manager: The ProjectStructureManager instance.
            file_renderer: The FileRenderer instance for rendering templates.
            requirements_manager: The RequirementsManager instance.
            options: Service-specific options for Docker (e.g., python_version, postgres_version).
        """
        super().__init__(structure_manager, file_renderer, requirements_manager, options) # Call super().__init__
        # Remove redundant assignments handled by base class
        # self.structure_manager = structure_manager
        # self.file_renderer = file_renderer
        # self.project_path = structure_manager.project_path
        # self.options = options or {} # Ensure options is a dictionary

        # Base directory for Docker templates
        # Assuming Docker templates are in a 'docker_template' subdirectory within the main template directory
        self.template_base_dir = 'docker_template'

    def generate(self) -> None:
        """
        Generates all Docker-related files.
        """
        # Create a dedicated directory for Docker-related files if needed (e.g., ./docker)
        # Although docker-compose.yml is often at the root, other files like Dockerfile
        # might be placed in a 'docker' subdirectory. Adjust as per your desired structure.
        docker_dir = self.project_path / 'docker'
        docker_dir.mkdir(exist_ok=True) # Ensure the directory exists

        # Get service dependencies to determine included services for docker-compose context
        # Access structure via self.structure_manager
        included_services = [s['name'] for s in self.structure_manager.structure.get('services', [])]

        docker_defaults = ConfigurationManager.get_service_default_options(self.service_name) # Use self.service_name
        # Get options with defaults
        python_version = self.options.get('python_version', docker_defaults.get('python_version', '3.9'))
        postgres_version = self.options.get('postgres_version', docker_defaults.get('postgres_version', '13'))
        # Add other Docker-specific options here as needed

        # Generate Dockerfile
        self._generate_dockerfile(docker_dir, python_version)

        # Generate docker-compose.yml
        self._generate_docker_compose(included_services, python_version, postgres_version)

        # Generate .dockerignore
        self._generate_dockerignore()


    def _generate_dockerfile(self, docker_dir: Path, python_version: str) -> None:
        """
        Generates the Dockerfile.

        Args:
            docker_dir: The Path object for the Docker directory.
            python_version: The Python version to use in the Dockerfile.
        """
        template_name = f'{self.template_base_dir}/Dockerfile.template'
        output_path = docker_dir / 'Dockerfile' # Place Dockerfile inside the docker directory

        context = {
            'python_version': python_version,
            'project_name': self.structure_manager.project_name,
            # Add other context variables needed for Dockerfile template
        }

        self.file_renderer.render_template(template_name, output_path, context)


    def _generate_docker_compose(self, included_services: list[str], python_version: str, postgres_version: str) -> None:
        """
        Generates the docker-compose.yml file.

        Args:
            included_services: List of service names included in the project.
            python_version: Python version for the app service.
            postgres_version: PostgreSQL version for the database service.
        """
        template_name = f'{self.template_base_dir}/docker-compose.yml.template'
        output_path = self.project_path / 'docker-compose.yml' # Place docker-compose.yml at project root

        # Determine which service configurations to include in docker-compose based on included_services
        use_celery = 'celery' in included_services
        use_redis = 'redis' in included_services
        # Add checks for other services that might need docker-compose entries

        context = {
            'project_name': self.structure_manager.project_name,
            'python_version': python_version,
            'postgres_version': postgres_version,
            'use_celery': use_celery,
            'use_redis': use_redis,
            # Add other context variables for docker-compose template (e.g., database credentials placeholders)
        }

        self.file_renderer.render_template(template_name, output_path, context)


    def _generate_dockerignore(self) -> None:
        """
        Generates the .dockerignore file.
        """
        template_name = f'{self.template_base_dir}/.dockerignore.template'
        output_path = self.project_path / '.dockerignore' # Place .dockerignore at project root

        # No specific context typically needed for a basic .dockerignore

        self.file_renderer.render_template(template_name, output_path)

