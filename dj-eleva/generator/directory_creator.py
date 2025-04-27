from pathlib import Path
from typing import Dict, Any, Optional

from core.configuration_manager import ConfigurationManager


class DirectoryCreator:
    """
    Handles the creation of directories for the Django project.
    """
    def __init__(self, project_path: Path, config_manager: Optional[ConfigurationManager] = None):
        """
        Initialize the DirectoryCreator.

        Args:
            project_path: The root path of the project.
            config_manager: Optional configuration manager instance.
        """
        self.project_path = project_path
        self.config_manager = config_manager or ConfigurationManager()

    def create_required_folders(self) -> None:
        """
        Creates the default required folders like static, media, etc.
        """
        project_structure = self.config_manager.project_structure
        if 'required_folders' in project_structure:
            for folder in project_structure['required_folders']:
                (self.project_path / folder).mkdir(parents=True, exist_ok=True)


    def create_custom_directories(self, custom_directories: Dict[str, Dict[str, Any]]) -> None:
        """
        Creates custom directories defined in the project structure.

        Args:
            custom_directories: A dictionary mapping directory paths to their info.
                               (e.g., {'my_app/sub_dir': {'name': 'sub_dir', 'parent': 'my_app', ...}})
        """
        for dir_path in sorted(custom_directories.keys()):
            full_dir_path = self.project_path / dir_path
            full_dir_path.mkdir(parents=True, exist_ok=True)