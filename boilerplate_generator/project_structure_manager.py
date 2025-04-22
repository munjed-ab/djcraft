from pathlib import Path
from typing import Dict, List, Optional

from config import Config
from exceptions import (
    InvalidAppNameError,
    InvalidDirectoryNameError,
    InvalidPathError,
    InvalidProjectNameError,
    StructureValidationError,
)
from rules import StructureRules


class ProjectStructureManager:
    """
    Manages the structure of a Django project with flexible directory layouts.
    """
    def __init__(self, project_name: str):
        """Initialize the project structure manager with a project name"""
        if not StructureRules.is_valid_project_name(project_name):
            raise InvalidProjectNameError(f"Invalid project name: {project_name}")
        
        self.project_name = project_name
        self.structure = {
            'directories': {},  # this all directory information
            'apps': {},         # mapping app name to its path
            'core': {           # core Django files configuration
                'location': Config.DEFAULT_PROJECT_STRUCTURE['core_location'],
                'path': 'core'
            },
            'services': []      # some services to include
        }
        self.project_path = Path(project_name)
    
    def add_directory(self, dir_name: str, parent_path: Optional[str] = None) -> str:
        """
        Add a directory to the project structure
        
        Args:
            dir_name: Name of the directory
            parent_path: Path to parent directory (None for root level)
            
        Returns:
            Full path to the created directory
        """
        if not StructureRules.is_valid_directory_name(dir_name):
            raise InvalidDirectoryNameError(f"Invalid directory name: {dir_name}")
        
        # if None -> top-level directory
        parent_path = parent_path or ""
        
        if parent_path:
            full_path = f"{parent_path}/{dir_name}"
        else:
            full_path = dir_name

        # TODO: maybe we can add dir with no rules???
        # if not StructureRules.can_add_directory(self.structure, full_path):
        #     raise StructureValidationError(
        #         f"Cannot add directory '{dir_name}' to path '{parent_path}'. "
        #         "Path may contain apps or conflict with existing structure."
        #     )
            
        # adding to structure
        if full_path not in self.structure['directories']:
            self.structure['directories'][full_path] = {
                'name': dir_name,
                'parent': parent_path,
                'apps': [],
                'subdirs': []
            }
            
            # update parent's subdirs if it exists
            if parent_path and parent_path in self.structure['directories']:
                self.structure['directories'][parent_path]['subdirs'].append(dir_name)
        
        return full_path
    
    def add_app(self, app_name: str, directory_path: str = "") -> None:
        """
        Add an app to a specific directory
        
        Args:
            app_name: Name of the Django app
            directory_path: Path where to create the app (empty for root)
        """
        if not StructureRules.is_valid_app_name(app_name):
            raise InvalidAppNameError(f"Invalid app name: {app_name}")
        
        if app_name in self.structure['apps']:
            raise StructureValidationError(f"App '{app_name}' already exists")
        
        if directory_path and directory_path not in self.structure['directories']:
            raise InvalidPathError(f"Directory path '{directory_path}' does not exist")
        
        # check if directory can contain apps
        if directory_path and not StructureRules.can_add_app_to_directory(
            self.structure, directory_path
        ):
            raise StructureValidationError(
                f"Cannot add app to directory '{directory_path}'"
            )
        
        app_path = f"{directory_path}/{app_name}" if directory_path else app_name
        self.structure['apps'][app_name] = app_path
        
        # adding app to directory's app list
        if directory_path:
            self.structure['directories'][directory_path]['apps'].append(app_name)
    
    def set_core_location(self, location_type: str, path: str) -> None:
        """
        Set the location for core Django files
        
        Args:
            location_type: Type of location ('root', 'custom')
            path: Path where to place core files
        """
        if location_type not in ["root", "custom"]:
            raise ValueError("Location type must be 'root', or 'custom'")
        
        # custom path -> validate the path
        if location_type == "custom":
            # path shouldn't be an app
            for app_name, app_path in self.structure['apps'].items():
                if path.startswith(app_path):
                    raise StructureValidationError(
                        f"Core location cannot be inside an app: {app_name}"
                    )
            
            parts = path.split('/')
            current_path = ""
            for part in parts:
                if current_path:
                    current_path = f"{current_path}/{part}"
                else:
                    current_path = part
                    
                if current_path not in self.structure['directories']:
                    try:
                        self.add_directory(part, current_path[:-len(part)-1] if current_path != part else "")
                    except Exception as e:
                        raise StructureValidationError(
                            f"Cannot create core path: {e}"
                        )

        self.structure['core']['location'] = location_type
        self.structure['core']['path'] = path
    
    def add_service(self, service_name: str, options: Optional[Dict] = None) -> None:
        """
        Add a service configuration to the project
        
        Args:
            service_name: Name of the service (e.g., 'docker', 'celery')
            options: Configuration options for the service
        """
        if service_name not in Config.AVAILABLE_SERVICES:
            raise ValueError(f"Unknown service: {service_name}")
        
        existing_services = [s['name'] for s in self.structure['services']]
        if service_name in existing_services:
            raise StructureValidationError(f"Service '{service_name}' already added")
        
        self.structure['services'].append({
            'name': service_name,
            'options': options or {}
        })

    def has_service(self, service_name):
        if service_name not in Config.AVAILABLE_SERVICES:
            return False
        return True
    
    def get_core_path(self) -> Path:
        """Get the full filesystem path for core files"""
        return self.project_path / self.structure['core']['path']
    
    def validate_structure(self) -> List[str]:
        """
        Validate the entire project structure
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not StructureRules.is_valid_project_name(self.project_name):
            errors.append(f"Invalid project name: {self.project_name}")
        
        for app_name, app_path in self.structure['apps'].items():
            if not StructureRules.is_valid_app_name(app_name):
                errors.append(f"Invalid app name: {app_name}")
                
            for other_app, other_path in self.structure['apps'].items():
                if app_name != other_app and app_path.startswith(f"{other_path}/"):
                    errors.append(f"App '{app_name}' cannot be inside app '{other_app}'")

        core_path = self.structure['core']['path']
        for app_name, app_path in self.structure['apps'].items():
            if core_path.startswith(f"{app_path}/"):
                errors.append(f"Core files cannot be inside app '{app_name}'")
        
        return errors
    
    def get_python_import_paths(self) -> Dict[str, str]:
        """
        Get Python import paths for all apps
        
        Returns:
            Dictionary mapping app name to import path
        """
        import_paths = {}
        for app_name, app_path in self.structure['apps'].items():
            import_path = app_path.replace('/', '.')
            import_paths[app_name] = import_path
        
        return import_paths