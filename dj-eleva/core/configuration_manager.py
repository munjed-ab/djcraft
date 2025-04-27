import os
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import DefaultSettings
from .exceptions import ConfigurationError
from .runtime_config import RuntimeConfig


class ConfigurationManager:
    """Manages the configuration system by merging default settings with runtime configurations."""

    def __init__(self, yaml_config_path: Optional[Path] = None):
        """Initialize the ConfigurationManager.

        Args:
            yaml_config_path: Optional path to a YAML configuration file.
        """
        self._default_settings = DefaultSettings()
        self._runtime_config = None
        if yaml_config_path:
            self.load_runtime_config(yaml_config_path)

    def load_runtime_config(self, yaml_path: Path) -> None:
        """Load runtime configuration from a YAML file.

        Args:
            yaml_path: Path to the YAML configuration file.

        Raises:
            ConfigurationError: If the YAML file is invalid or cannot be loaded.
        """
        try:
            self._runtime_config = RuntimeConfig.from_yaml(yaml_path)
        except ConfigurationError as e:
            raise ConfigurationError(f"Failed to load runtime configuration: {e}")

    @property
    def project_structure(self) -> Dict[str, Any]:
        """Get project structure configuration.

        Returns:
            Merged project structure configuration.
        """
        if self._runtime_config:
            return asdict(self._runtime_config.project_structure)
        return asdict(self._default_settings.PROJECT_STRUCTURE)

    @property
    def files(self) -> Dict[str, Any]:
        """Get files configuration.

        Returns:
            Merged files configuration.
        """
        if self._runtime_config:
            return asdict(self._runtime_config.files)
        return asdict(self._default_settings.DEFAULT_FILES)

    @property
    def template(self) -> Dict[str, Any]:
        """Get template configuration.

        Returns:
            Merged template configuration.
        """
        if self._runtime_config:
            return asdict(self._runtime_config.template)
        return asdict(self._default_settings.TEMPLATE_CONFIG)

    @property
    def django(self) -> Dict[str, Any]:
        """Get Django configuration.

        Returns:
            Merged Django configuration.
        """
        if self._runtime_config:
            return asdict(self._runtime_config.django)
        return asdict(self._default_settings.DJANGO_DEFAULTS)

    @property
    def cli(self) -> Dict[str, Any]:
        """Get CLI configuration.

        Returns:
            Merged CLI configuration.
        """
        if self._runtime_config:
            return asdict(self._runtime_config.cli)
        return asdict(self._default_settings.CLI_DEFAULTS)

    def get_service_info(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific service.

        Args:
            service_name: The name of the service.

        Returns:
            Service information dictionary or None if not found.
        """
        available_services = self._default_settings.AVAILABLE_SERVICES
        if hasattr(available_services, service_name):
            service_info = getattr(available_services, service_name)
            return asdict(service_info) if service_info else None
        return None

    def get_service_dependencies(self, service_name: str) -> List[str]:
        """Get dependencies for a specific service.

        Args:
            service_name: The name of the service.

        Returns:
            List of service dependencies.
        """
        service_info = self.get_service_info(service_name)
        return service_info.get('dependencies', []) if service_info else []

    def get_service_default_options(self, service_name: str) -> Dict[str, Any]:
        """Get default options for a specific service.

        Args:
            service_name: The name of the service.

        Returns:
            Dictionary of default service options.
        """
        service_info = self.get_service_info(service_name)
        return service_info.get('default_options', {}) if service_info else {}
    
    def get_template_path(self, template_name: str) -> str:
        """
        Get the full path to a template file.

        Args:
            template_name: The name of the template file relative to the base template directory.

        Returns:
            The absolute path to the template file.
        """
        template_config = self.template
        return os.path.join(template_config['template_dir'], template_name)

    def get_default_files(self, component_type: str) -> List[str]:
        """
        Get the list of default files for a given component type.

        Args:
            component_type: The type of component ('project', 'core', 'app', etc.).

        Returns:
            A list of default file names.
        """
        files_config = self.files
        return files_config.get(component_type, [])
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        Get complete configuration as a unified dictionary.
        
        Returns:
            Dictionary containing all configuration settings.
        """
        config = {
            'project_structure': self.project_structure,
            'files': self.files,
            'template': self.template,
            'django': self.django,
            'cli': self.cli,
        }
        
        if self._runtime_config:
            # Add any additional sections from runtime config
            for key, value in self._runtime_config.to_dict().items():
                if key not in config:
                    config[key] = value
                    
        return config
    
    def get_available_services(self) -> List[str]:
        """
        Get list of all available service names.
        
        Returns:
            List of service names.
        """
        return self._default_settings.AVAILABLE_SERVICES.get_service_names()