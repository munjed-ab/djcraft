import json
import os
from pathlib import Path
from typing import Dict, List

import yaml
from core.configuration_manager import ConfigurationManager
from core.project_structure_manager import ProjectStructureManager
from core.rules import StructureRules


def load_config_file(config_path: str) -> Dict:
    """
    Load configuration from YAML or JSON file
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing the configuration
    """
    with open(config_path, 'r') as f:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            config = yaml.safe_load(f)
        elif config_path.endswith('.json'):
            config = json.load(f)
        else:
            raise ValueError("Config file must be YAML or JSON")

    return config


def validate_config(config) -> List[str]:
    """
    Validate configuration without creating project
    
    Args:
        config: Configuration file dictionary
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    if 'project_name' not in config:
        errors.append("Missing required field: project_name")
        return errors

    project_name = config['project_name']
    if not project_name:
        errors.append("Project name cannot be empty")

    # Create temporary structure manager for validation
    try:
        structure_manager = ProjectStructureManager(project_name)

        # Validate core configuration
        errors.extend(_validate_core_config(config, structure_manager))
        
        # Validate directories
        errors.extend(_validate_directories_config(config))
        
        # Validate apps
        errors.extend(_validate_apps_config(config))
        
        # Validate services
        errors.extend(_validate_services_config(config))

    except Exception as e:
        errors.append(f"Configuration error: {e}")

    return errors


def _validate_core_config(config, structure_manager: ProjectStructureManager) -> List[str]:
    """Validate core configuration"""
    errors = []
    config = config.get_all_config()
    core_config = config['core'] or {}
    core_location = core_config['location'] or config['project_structure']['core_location']
    core_path = core_config['path'] or config['project_structure']['core_path']

    try:
        structure_manager.set_core_location(core_location, core_path)
    except Exception as e:
        errors.append(f"Invalid core configuration: {e}")
        
    return errors


def _validate_directories_config(config) -> List[str]:
    """Validate directories configuration"""
    errors = []
    config = config.get_all_config()
    directories = config['directories'] or []
    for directory in directories:
        name = directory['name']
        _ = directory['parent'] or ""

        if not name:
            errors.append("Directory missing name")
            continue

        try:
            if not StructureRules.is_valid_directory_name(name):
                errors.append(f"Invalid directory name '{name}'")
        except Exception as e:
            errors.append(f"Invalid directory '{name}': {e}")
            
    return errors


def _validate_apps_config(config: Dict) -> List[str]:
    """Validate apps configuration"""
    errors = []
    config = config.get_all_config()
    apps = config['apps'] or []
    for app in apps:
        name = app['name']
        _ = app['directory'] or ""

        if not name:
            errors.append("App missing name")
            continue

        try:
            if not StructureRules.is_valid_app_name(name):
                errors.append(f"Invalid app name '{name}'")
        except Exception as e:
            errors.append(f"Invalid app '{name}': {e}")
            
    return errors


def _validate_services_config(config: Dict) -> List[str]:
    """Validate services configuration"""
    errors = []
    config = config.get_all_config()
    services = config['services'] or []
    existing_service_names = []
    
    for service in services:
        name = service['name']
        _ = service['options'] or {}

        if not name:
            errors.append("Service missing name")
            continue

        if name not in ConfigurationManager().get_available_services():
            errors.append(f"Unknown service: {name}")
            continue

        try:
            if not StructureRules.validate_service_compatibility(name, existing_service_names):
                errors.append(f"Service '{name}' has compatibility issues with existing services.")

            existing_service_names.append(name)
        except Exception as e:
            errors.append(f"Invalid service '{name}': {e}")
            
    return errors


def save_configuration(structure_manager: ProjectStructureManager, config_path: str) -> None:
    """
    Save the current project structure configuration to a YAML or JSON file
    
    Args:
        structure_manager: Project structure manager
        config_path: Path where to save the configuration file
    """
    internal_structure = structure_manager.structure
    external_config_data = {
        'project_name': structure_manager.project_name,
        'core': internal_structure['core'],
        'directories': [],
        'apps': [],
        'services': internal_structure['services'],
        'env': internal_structure.get('env', 'dev')
    }

    for dir_path in sorted(internal_structure['directories'].keys()):
        dir_info = internal_structure['directories'][dir_path]
        external_config_data['directories'].append({
            'name': dir_info['name'],
            'parent': dir_info.get('parent', '')
        })

    for app_name in sorted(internal_structure['apps'].keys()):
        app_path = internal_structure['apps'][app_name]
        external_config_data['apps'].append({
            'name': app_name,
            'directory': str(Path(app_path).parent) if Path(app_path).parent != Path('.') else ''
        })

    output_dir = Path(config_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            _save_yaml_config(config_path, external_config_data)
        elif config_path.endswith('.json'):
            _save_json_config(config_path, external_config_data)
        else:
            raise ValueError("Config file must have a .yaml, .yml, or .json extension")
    except Exception as e:
        raise DjangoBoilerplateError(f"Failed to save configuration: {e}")


def _save_yaml_config(config_path: str, data: Dict) -> None:
    """Save configuration as YAML with comments"""
    with open(config_path, 'w') as f:
        f.write("# Required: The name of your Django project\n")
        yaml.dump({'project_name': data['project_name']}, f, indent=2, default_flow_style=False)
        f.write("\n# Optional: Configure the core Django files location\n")
        yaml.dump({'core': data['core']}, f, indent=2, default_flow_style=False)
        f.write("\n# Optional: Define directories\n")
        yaml.dump({'directories': data['directories']}, f, indent=2, default_flow_style=False)
        f.write("\n# Optional: Define apps and their directories\n")
        yaml.dump({'apps': data['apps']}, f, indent=2, default_flow_style=False)
        f.write("\n# Optional: Define services and their options\n")
        yaml.dump({'services': data['services']}, f, indent=2, default_flow_style=False)
        f.write("\n# Optional: Environment setting (used in settings/__init__.py)\n")
        yaml.dump({'env': data['env']}, f, indent=2, default_flow_style=False)
        
        _flush_buffer(f)


def _save_json_config(config_path: str, data: Dict) -> None:
    """Save configuration as JSON"""
    with open(config_path, 'w') as f:
        json.dump(data, f, indent=2)
        _flush_buffer(f)


def _flush_buffer(file) -> None:
    """Attempt to flush file buffer and sync to disk"""
    try:
        file.flush()
        os.fsync(file.fileno())
    except Exception as e:
        print(f"Warning: Could not fully flush buffer for file {file.name}: {e}")
