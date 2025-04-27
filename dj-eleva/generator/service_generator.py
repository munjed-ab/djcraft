import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, Type

from core.configuration_manager import ConfigurationManager
from core.exceptions import DependencyError
from core.project_structure_manager import ProjectStructureManager

from .file_renderer import FileRenderer
from .requirements_manager import RequirementsManager
from .services.base import BaseServiceGenerator


class ServiceGenerator:
    """
    Manages and dispatches the generation of configurations for various services.
    Dynamically loads service generators from the 'services' subdirectory.
    """
    def __init__(self, structure_manager: ProjectStructureManager, file_renderer: FileRenderer, requirements_manager: RequirementsManager):
        """
        Initialize the ServiceGenerator.

        Args:
            structure_manager: The ProjectStructureManager instance.
            file_renderer: The FileRenderer instance for rendering templates.
            requirements_manager: The RequirementsManager instance for managing dependencies.
        """
        self.structure_manager = structure_manager
        self.file_renderer = file_renderer
        self.requirements_manager = requirements_manager
        self.project_path = structure_manager.project_path

        self.service_generators = self._discover_service_generators()

    def _discover_service_generators(self) -> Dict[str, Type[BaseServiceGenerator]]:
        """
        Dynamically discovers and loads service generator classes
        from the 'generator/services' directory.
        """
        generators = {}
        services_package_path = Path(__file__).parent / 'services'
        services_module_prefix = f"{__package__}.services."

        for finder, name, ispkg in pkgutil.iter_modules([str(services_package_path)]):
            if not ispkg and name not in ('__init__', 'base'): # Skip packages, __init__, and base
                module_name = f"{services_module_prefix}{name}"
                try:
                    module = importlib.import_module(module_name)
                    for class_name, obj in inspect.getmembers(module, inspect.isclass):
                        # Check if it's a subclass of BaseServiceGenerator
                        # and not BaseServiceGenerator itself
                        if issubclass(obj, BaseServiceGenerator) and obj is not BaseServiceGenerator:
                            if hasattr(obj, 'service_name') and obj.service_name:
                                if obj.service_name in generators:
                                    print(f"Warning: Duplicate service name '{obj.service_name}' found in {module_name}. Overwriting.")
                                generators[obj.service_name] = obj
                            else:
                                print(f"Warning: Service generator {class_name} in {module_name} is missing the 'service_name' attribute. Skipping.")
                except ImportError as e:
                    print(f"Warning: Could not import service module '{module_name}': {e}")
                except Exception as e:
                    print(f"Warning: Error loading service generator from '{module_name}': {e}")

        return generators


    def generate(self) -> None:
        """
        Generates configurations for all services specified in the project structure.
        """
        services_to_generate = self.structure_manager.structure.get('services', [])

        for service_config in services_to_generate:
            service_name = service_config.get('name')
            service_options = service_config.get('options', {})

            if not service_name:
                print("Warning: Skipping service with missing name in configuration.")
                continue
            try:
                self._check_service_dependencies(service_name)
            except DependencyError as e:
                print(f"Error generating service '{service_name}': {e}")
                continue

            generator_class = self.service_generators.get(service_name)

            if generator_class:
                try:
                    service_gen_instance = generator_class(
                        self.structure_manager,
                        self.file_renderer,
                        self.requirements_manager,
                        service_options
                    )
                    service_gen_instance.generate()
                    print(f"Generated configuration for service: {service_name}")
                except Exception as e:
                    print(f"Error generating configuration for service '{service_name}': {e}")
            else:
                print(f"Warning: No generator found for service '{service_name}'. Skipping.")


    def _check_service_dependencies(self, service_name: str) -> None:
        """
        Check if all dependencies for a service are included in the structure manager.

        Args:
            service_name: Name of the service to check.

        Raises:
            DependencyError: If a required dependency is not found.
        """
        dependencies = ConfigurationManager.get_service_dependencies(service_name)
        # Ensure get_services() returns a list of dicts with 'name'
        existing_services = [s.get('name') for s in self.structure_manager.get_services() if isinstance(s, dict) and 'name' in s]

        for dep in dependencies:
            if dep not in existing_services:
                raise DependencyError(
                    f"Service '{service_name}' requires '{dep}' which is not included in the project configuration."
                )

