import re
from typing import Dict, List


class StructureRules:
    """
    Rules for validating Django project structure elements.
    """
    PROJECT_NAME_REGEX = r'^[a-zA-Z][a-zA-Z0-9_]+$'
    APP_NAME_REGEX = r'^[a-z][a-z0-9_]+$'
    DIRECTORY_NAME_REGEX = r'^[a-zA-Z][a-zA-Z0-9_-]+$'
    RESERVED_NAMES = {
        'django', 'test', 'settings', 'setup', 'admin', 'auth',
        'contenttypes', 'sessions', 'messages', 'static', 'staticfiles'
    }
    
    @classmethod
    def is_valid_project_name(cls, name: str) -> bool:
        """Check if project name is valid"""
        if name.lower() in cls.RESERVED_NAMES:
            return False
        return bool(re.match(cls.PROJECT_NAME_REGEX, name))
    
    @classmethod
    def is_valid_app_name(cls, name: str) -> bool:
        """Check if app name is valid"""
        if name.lower() in cls.RESERVED_NAMES:
            return False
        return bool(re.match(cls.APP_NAME_REGEX, name))
    
    @classmethod
    def is_valid_directory_name(cls, name: str) -> bool:
        """Check if directory name is valid"""
        if name.lower() in cls.RESERVED_NAMES:
            return False
        return bool(re.match(cls.DIRECTORY_NAME_REGEX, name))
    
    # @classmethod
    # def can_add_directory(cls, structure: Dict, path: str) -> bool:
    #     """
    #     Check if a directory can be added at the given path
        
    #     Args:
    #         structure: Current project structure
    #         path: Path where directory would be added
            
    #     Returns:
    #         True if directory can be added, False otherwise
    #     """
    #     for app_name, app_path in structure['apps'].items():
    #         # if the path is inside an app directory
    #         if path.startswith(f"{app_path}/"):
    #             return False
    #         # if the path dir would contain an app
    #         if app_path.startswith(f"{path}/"):
    #             return False
                
    #     #  already exists
    #     if path in structure['directories']:
    #         return False
            
    #     return True
    
    @classmethod
    def can_add_app_to_directory(cls, structure: Dict, dir_path: str) -> bool:
        """
        Check if an app can be added to a directory
        
        Args:
            structure: Current project structure
            dir_path: Path of directory where app would be added
            
        Returns:
            True if an app can be added, False otherwise
        """
        if dir_path and dir_path not in structure['directories']:
            return False
            
        # chevck if path is inside an app
        for app_name, app_path in structure['apps'].items():
            if dir_path.startswith(f"{app_path}/"):
                return False
                
        return True
    
    @classmethod
    def validate_service_compatibility(cls, service_name: str, existing_services: List[str]) -> bool:
        """
        Check if a new service is compatible with existing services
        
        Args:
            service_name: Name of service to add
            existing_services: List of existing service names
            
        Returns:
            True if service is compatible, False otherwise
        """
        # define service dependencies and conflicts
        dependencies = {
            'celery': ['redis'],
        }
        
        conflicts = {
        }
        if service_name in dependencies:
            for dep in dependencies[service_name]:
                if dep not in existing_services:
                    return False

        if service_name in conflicts:
            for conflict in conflicts[service_name]:
                if conflict in existing_services:
                    return False
                    
        return True