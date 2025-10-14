from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml

from .config import (
    CliDefaultSettings,
    DefaultSettings,
    DjangoDefaultsSettings,
    FilesDefaultSettings,
    ProjectStructureDefaultSettings,
    TemplateDefaultSettings,
)
from .exceptions import ConfigurationError


@dataclass
class RuntimeConfig:
    """Handles dynamic configurations loaded from YAML files."""
    project_structure: ProjectStructureDefaultSettings
    files: FilesDefaultSettings
    template: TemplateDefaultSettings
    django: DjangoDefaultsSettings
    cli: CliDefaultSettings
    directories: List[Dict[str, str]] = field(default_factory=list)
    apps: List[Dict[str, str]] = field(default_factory=list)
    services: List[Dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'RuntimeConfig':
        """Load configuration from a YAML file and merge with default settings."""
        try:
            with open(yaml_path, 'r') as f:
                yaml_config = yaml.safe_load(f)

            if not isinstance(yaml_config, dict):
                raise ConfigurationError("YAML configuration must be a dictionary")

            config = {
                'project_structure': asdict(DefaultSettings.PROJECT_STRUCTURE),
                'files': asdict(DefaultSettings.DEFAULT_FILES),
                'template': asdict(DefaultSettings.TEMPLATE_CONFIG),
                'django': asdict(DefaultSettings.DJANGO_DEFAULTS),
                'cli': asdict(DefaultSettings.CLI_DEFAULTS),
                'directories': [],
                'apps': [],
                'services': []
            }

            if 'project_name' in yaml_config:
                config['cli']['project_name'] = yaml_config['project_name']

            if 'core' in yaml_config:
                if 'location' in yaml_config['core']:
                    config['project_structure']['core_location'] = yaml_config['core']['location']
                if 'path' in yaml_config['core']:
                    config['project_structure']['core_path'] = yaml_config['core']['path']

            if 'directories' in yaml_config:
                config['directories'] = yaml_config['directories']
            
            if 'apps' in yaml_config:
                config['apps'] = yaml_config['apps']
                
            if 'services' in yaml_config:
                config['services'] = yaml_config['services']

            # merge additional sections from YAML
            for section in ['project_structure', 'files', 'template', 'django', 'cli']:
                if section in yaml_config:
                    config[section].update(yaml_config[section])

            # create RuntimeConfig instance
            return cls(
                project_structure=ProjectStructureDefaultSettings(**config['project_structure']),
                files=FilesDefaultSettings(**config['files']),
                template=TemplateDefaultSettings(**config['template']),
                django=DjangoDefaultsSettings(**config['django']),
                cli=CliDefaultSettings(**config['cli']),
                directories=config['directories'],
                apps=config['apps'],
                services=config['services']
            )

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the RuntimeConfig to a dictionary."""
        return {
            'project_structure': asdict(self.project_structure),
            'files': asdict(self.files),
            'template': asdict(self.template),
            'django': asdict(self.django),
            'cli': asdict(self.cli),
            'directories': self.directories,
            'apps': self.apps,
            'services': self.services
        }
