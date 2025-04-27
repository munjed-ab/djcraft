import os
import sys

from core.configuration_manager import ConfigurationManager
from core.project_structure_manager import ProjectStructureManager
from generator.base_generator import DjangoProjectGenerator

from .config_io import validate_config
from .interactive.ui import preview_structure


def handle_create_command(args):
    """
    Handle the create command
    
    Args:
        args: Command line arguments
        
    Returns:
        ProjectStructureManager: Configured structure manager
    """
    structure_manager = ProjectStructureManager(args.project_name)

    if args.core_location == 'custom':
        if not args.core_path:
            raise ValueError("--core-path is required when --core-location=custom")
        structure_manager.set_core_location(args.core_location, args.core_path)

    for dir_spec in args.directories:
        if ':' in dir_spec:
            name, parent = dir_spec.split(':', 1)
        else:
            name, parent = dir_spec, ""
        structure_manager.add_directory(name, parent)

    for app in args.apps:
        app_dir = ""
        for app_dir_spec in args.app_directories:
            app_name, dir_path = app_dir_spec.split(':', 1)
            if app_name == app:
                app_dir = dir_path
                break

        structure_manager.add_app(app, app_dir)

    for service in args.services:
        # Get default options and merge/override with provided options
        default_options = ConfigurationManager.get_service_default_options(service)
        provided_options = args.service_options.get(service, {})
        options = {**default_options, **provided_options} # Merge, provided overrides default
        structure_manager.add_service(service, options)

    generator = DjangoProjectGenerator(structure_manager)
    generator.generate()

    return structure_manager


def handle_generate_from_config(config_path):
    """
    Handle project generation from config file
    
    Args:
        config_path: Path to config file
        
    Returns:
        ProjectStructureManager: Configured structure manager
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    config = ConfigurationManager(config_path)
    structure_manager = create_project_from_config(config)
    
    return structure_manager


def handle_validate_command(config_path, console=None, rich_available=False):
    """
    Handle validation of a configuration file
    
    Args:
        config_path: Path to config file
        console: Rich console if available
        rich_available: Whether Rich is available
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    config = ConfigurationManager(config_path)
    errors = validate_config(config)

    if errors:
        if console:
            console.print("[bold red]Configuration validation failed:[/bold red]")
            for error in errors:
                console.print(f"[bold red]  - {error}[/bold red]")
        else:
            print("Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
        sys.exit(1)
    else:
        if console:
            console.print("[bold green]Configuration is valid![/bold green]")
        else:
            print("Configuration is valid!")

        if rich_available:
            from rich.prompt import Confirm
            if Confirm.ask("[bold blue]Show structure preview?[/bold blue]"):
                structure_manager = create_project_structure_from_config(config, preview_only=True)
                preview_structure(structure_manager, console)


def create_project_from_config(config):
    """
    Create project from configuration
    
    Args:
        config: Project configuration dictionary
        
    Returns:
        ProjectStructureManager: Project structure manager
    """
    structure_manager = create_project_structure_from_config(config)
    project_name = structure_manager.project_name
    if not project_name:
        raise ValueError("Missing project name in configuration")

    generator = DjangoProjectGenerator(structure_manager, config)
    generator.generate()

    return structure_manager


def create_project_structure_from_config(config_manager, preview_only=False):
    """
    Create project structure from configuration
    
    Args:
        config_manager: ConfigurationManager instance
        preview_only: Whether this is just for preview
        
    Returns:
        ProjectStructureManager: Configured structure manager
    """
    # Get all configuration as a single dictionary
    config = config_manager.get_all_config()
    
    project_name = config['cli']['project_name']
    structure_manager = ProjectStructureManager(project_name)

    # Set core location
    core_location = config['project_structure']['core_location']
    core_path = config['project_structure']['core_path']
    structure_manager.set_core_location(core_location, core_path)

    # Create directories
    directories = config['directories'] or []
    for directory in directories:
        name = directory['name']
        parent = directory['parent'] or ""
        try:
            structure_manager.add_directory(name, parent)
        except Exception as e:
            print(f"Warning: Could not add directory '{name}': {e}")

    # Create apps
    apps = config['apps'] or []
    for app in apps:
        name = app['name']
        directory = app['directory'] or ""
        try:
            structure_manager.add_app(name, directory)
        except Exception as e:
            print(f"Warning: Could not add app '{name}': {e}")

    # Add services if not preview mode
    if not preview_only:
        services = config['services'] or []
        for service in services:
            name = service['name']
            # Get default options and merge/override with config options
            default_options = config_manager.get_service_default_options(name)
            provided_options = service['options'] or {}
            options = {**default_options, **provided_options}  # Merge, provided overrides default
            
            try:
                structure_manager.add_service(name, options)
            except Exception as e:
                print(f"Warning: Could not add service '{name}': {e}")

    return structure_manager