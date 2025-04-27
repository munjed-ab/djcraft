# generator/abstract_generator.py
from abc import ABC, abstractmethod
from typing import Any, Dict

from core.configuration_manager import ConfigurationManager
from core.project_structure_manager import ProjectStructureManager

from .file_renderer import FileRenderer
from .requirements_manager import RequirementsManager


class AbstractGenerator(ABC):
    """Abstract base class for all generators implementing the Template Method pattern."""

    def __init__(self, structure_manager: ProjectStructureManager, 
                 file_renderer: FileRenderer,
                 requirements_manager: RequirementsManager,
                 config = None):
        """
        Initialize the AbstractGenerator.

        Args:
            structure_manager: The ProjectStructureManager instance.
            file_renderer: The FileRenderer instance for rendering templates.
            requirements_manager: The RequirementsManager instance.
            config: Optional configuration dictionary.
        """
        self.structure_manager = structure_manager
        self.file_renderer = file_renderer
        self.requirements_manager = requirements_manager
        self.project_path = structure_manager.project_path
        self.project_name = structure_manager.project_name
        self.config = config or ConfigurationManager()

    def generate(self) -> None:
        """Template method that defines the generation process workflow."""
        self.pre_generation()
        self.create_directories()
        self.generate_files()
        self.post_generation()

    def pre_generation(self) -> None:
        """Hook method for pre-generation tasks. Can be overridden by subclasses."""
        pass

    @abstractmethod
    def create_directories(self) -> None:
        """Create necessary directories for the generator. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def generate_files(self) -> None:
        """Generate files. Must be implemented by subclasses."""
        pass

    def post_generation(self) -> None:
        """Hook method for post-generation tasks. Can be overridden by subclasses."""
        pass

    def get_context(self) -> Dict[str, Any]:
        """Get the base context for template rendering."""
        return {
            'project_name': self.project_name,
            'config': self.config
        }