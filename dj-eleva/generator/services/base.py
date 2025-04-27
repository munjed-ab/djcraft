# generator/services/base.py
import abc
from typing import Any, Dict

# Forward references for type hinting if needed, or import directly
# from core.project_structure_manager import ProjectStructureManager
# from ..file_renderer import FileRenderer
# from ..requirements_manager import RequirementsManager

class BaseServiceGenerator(abc.ABC):
    """
    Abstract base class for all service generators.
    Ensures a consistent interface for initialization and generation.
    """
    # Define a class attribute to hold the service name key used in config
    # This makes discovery easier and decouples it from the class name.
    service_name = ""

    def __init__(self, structure_manager: Any, file_renderer: Any, requirements_manager: Any, options: Dict[str, Any]):
        """
        Initialize the service generator.

        Args:
            structure_manager: The ProjectStructureManager instance.
            file_renderer: The FileRenderer instance for rendering templates.
            requirements_manager: The RequirementsManager instance.
            options: Service-specific options dictionary.
        """
        self.structure_manager = structure_manager
        self.file_renderer = file_renderer
        self.requirements_manager = requirements_manager
        self.options = options or {}
        self.project_path = structure_manager.project_path

        if not self.service_name:
            raise NotImplementedError(f"Service generator {self.__class__.__name__} must define a 'service_name' class attribute.")


    @abc.abstractmethod
    def generate(self) -> None:
        """
        Abstract method to generate the specific service's files and configurations.
        """
        pass
