import argparse
import json
import os
import sys

import yaml

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, IntPrompt, Prompt
    from rich.table import Table
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from config import Config
from exceptions import DjangoBoilerplateError
from generator import DjangoProjectGenerator
from project_structure_manager import ProjectStructureManager


class DjangoBoilerplateCLI:
    """
    Command Line Interface for Django Boilerplate Generator
    """
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.structure_manager = None
        
    def run(self):
        """Main entry point for the CLI"""
        parser = self._create_argument_parser()
        args = parser.parse_args()
        
        if args.command == 'create':
            self._handle_create_command(args)
        elif args.command == 'interactive':
            self._handle_interactive_mode()
        elif args.command == 'generate':
            self._handle_generate_from_config(args)
        elif args.command == 'validate':
            self._handle_validate_command(args)
        else:
            parser.print_help()
    
    def _create_argument_parser(self):
        """Create argument parser for CLI"""
        parser = argparse.ArgumentParser(
            description='Django Project Boilerplate Generator',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Command to execute')
        
        create_parser = subparsers.add_parser('create', help='Create a new Django project')
        create_parser.add_argument('project_name', help='Name of the Django project')
        create_parser.add_argument(
            '--apps',
            nargs='+',
            default=[],
            help='List of apps to create'
        )
        create_parser.add_argument(
            '--dir',
            action='append',
            dest='directories',
            default=[],
            help='Add directories to project (can be used multiple times). Format: name:parent'
        )
        create_parser.add_argument(
            '--app-dir',
            action='append',
            dest='app_directories',
            default=[],
            help='Place apps in directories. Format: app_name:directory_path'
        )
        create_parser.add_argument(
            '--core-location',
            choices=['root', 'custom'],
            default=Config.DEFAULT_PROJECT_STRUCTURE['core_location'],
            help='Location of core configuration'
        )
        create_parser.add_argument(
            '--core-path',
            help='Custom path for core files (when --core-location=custom)'
        )
        create_parser.add_argument(
            '--services',
            nargs='+',
            choices=list(Config.AVAILABLE_SERVICES.keys()),
            default=[],
            help='Services to include in the project'
        )
        create_parser.add_argument(
            '--service-options',
            type=json.loads,
            default={},
            help='JSON string with service options'
        )
        
        interactive_parser = subparsers.add_parser(
            'interactive',
            help='Create a project in interactive mode'
        )
        
        generate_parser = subparsers.add_parser(
            'generate',
            help='Generate project from config file'
        )
        generate_parser.add_argument(
            'config_file',
            help='Path to YAML or JSON configuration file'
        )
        
        validate_parser = subparsers.add_parser(
            'validate',
            help='Validate project configuration file without generating'
        )
        validate_parser.add_argument(
            'config_file',
            help='Path to YAML or JSON configuration file to validate'
        )
        
        return parser
    
    def _handle_create_command(self, args):
        """Handle the create command"""
        try:
            self.structure_manager = ProjectStructureManager(args.project_name)
            
            if args.core_location == 'custom':
                if not args.core_path:
                    raise ValueError("--core-path is required when --core-location=custom")
                self.structure_manager.set_core_location(args.core_location, args.core_path)

            # add directories
            for dir_spec in args.directories:
                if ':' in dir_spec:
                    name, parent = dir_spec.split(':', 1)
                else:
                    name, parent = dir_spec, ""
                self.structure_manager.add_directory(name, parent)
            
            # add apps
            for app in args.apps:
                app_dir = ""
                # check if app should be placed in a specific directory
                for app_dir_spec in args.app_directories:
                    app_name, dir_path = app_dir_spec.split(':', 1)
                    if app_name == app:
                        app_dir = dir_path
                        break
                
                self.structure_manager.add_app(app, app_dir)
            
            # add services with options
            for service in args.services:
                options = args.service_options.get(service, {})
                self.structure_manager.add_service(service, options)
            
            # gen project
            generator = DjangoProjectGenerator(self.structure_manager)
            generator.generate_project()
            
            self._print_success(f"Django project '{args.project_name}' created successfully!")
            
        except DjangoBoilerplateError as e:
            self._print_error(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            self._print_error(f"Unexpected error: {e}")
            sys.exit(1)

    def _print_error(self, message):
        self.console.print(f"[bold red]{message}[/bold red]")

    def _print_success(self, message):
        self.console.print(f"[bold green]{message}[/bold green]")

    def _handle_interactive_mode(self):
        """Handle interactive project creation mode"""
        if not RICH_AVAILABLE:
            print("Rich library is required for interactive mode.")
            print("Install it with: pip install rich")
            sys.exit(1)
        
        try:
            self._print_welcome()
            
            project_name = Prompt.ask(
                "[bold blue]Enter project name[/bold blue]",
                default=Config.CLI_DEFAULTS['project_name']
            )
            
            self.structure_manager = ProjectStructureManager(project_name)
            
            self._interactive_menu()
            
            if Confirm.ask("[bold green]Generate project now?[/bold green]"):
                # show final structure preview
                self._preview_structure()
                
                if Confirm.ask("[bold green]Proceed with generation?[/bold green]"):
                    generator = DjangoProjectGenerator(self.structure_manager)
                    generator.generate_project()
                    self._print_success(f"Django project '{project_name}' created successfully!")
            else:
                # save configuration to a file
                if Confirm.ask("[bold blue]Save configuration to file?[/bold blue]"):
                    config_path = Prompt.ask(
                        "[bold blue]Enter file path to save configuration[/bold blue]",
                        default=f"{project_name}_config.yaml"
                    )
                    # TODO:
                    # self._save_configuration(config_path)
                    self._print_success(f"Configuration saved to {config_path}")
            
        except DjangoBoilerplateError as e:
            self._print_error(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            self._print_error(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def _handle_generate_from_config(self, args):
        """Handle project generation from config file"""
        try:
            config_path = args.config_file
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path}")
            
            config = self._load_config_file(config_path)
            self._create_project_from_config(config)
            
        except DjangoBoilerplateError as e:
            self._print_error(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            self._print_error(f"Unexpected error: {e}")
            sys.exit(1)
    
    def _handle_validate_command(self, args):
        """Handle validation of a configuration file"""
        try:
            config_path = args.config_file
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file not found: {config_path}")
            
            config = self._load_config_file(config_path)   
            # validate configuration from confiog file
            errors = self._validate_config(config)
            
            if errors:
                self._print_error("Configuration validation failed:")
                for error in errors:
                    self._print_error(f"  - {error}")
                sys.exit(1)
            else:
                self._print_success("Configuration is valid!")
                
                if RICH_AVAILABLE and Confirm.ask("[bold blue]Show structure preview?[/bold blue]"):
                    self._create_project_structure_from_config(config, preview_only=True)
                    # self._preview_structure()
            
        except Exception as e:
            self._print_error(f"Validation error: {e}")
            sys.exit(1)
    
    def _load_config_file(self, config_path):
        """Load configuration from YAML or JSON file"""
        with open(config_path, 'r') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                config = yaml.safe_load(f)
            elif config_path.endswith('.json'):
                config = json.load(f)
            else:
                raise ValueError("Config file must be YAML or JSON")
        
        return config
    
    def _validate_config(self, config):
        """Validate configuration without creating project"""
        errors = []
        
        if 'project_name' not in config:
            errors.append("Missing required field: project_name")
            return errors
        
        project_name = config.get('project_name')
        if not project_name:
            errors.append("Project name cannot be empty")
        
        # create temporary structure manager for validation
        try:
            structure_manager = ProjectStructureManager(project_name)
            
            core_config = config.get('core', {})
            core_location = core_config.get('location', Config.DEFAULT_PROJECT_STRUCTURE['core_location'])
            core_path = core_config.get('path', 'core')
            
            try:
                structure_manager.set_core_location(core_location, core_path)
            except Exception as e:
                errors.append(f"Invalid core configuration: {e}")
            
            # validete directories
            directories = config.get('directories', [])
            for directory in directories:
                name = directory.get('name')
                parent = directory.get('parent', "")
                
                if not name:
                    errors.append("Directory missing name")
                    continue
                
                try:
                    structure_manager.add_directory(name, parent)
                except Exception as e:
                    errors.append(f"Invalid directory '{name}': {e}")
            
            # validate apps
            apps = config.get('apps', [])
            for app in apps:
                name = app.get('name')
                directory = app.get('directory', "")
                
                if not name:
                    errors.append("App missing name")
                    continue
                
                try:
                    structure_manager.add_app(name, directory)
                except Exception as e:
                    errors.append(f"Invalid app '{name}': {e}")
            
            # calidate services
            services = config.get('services', [])
            for service in services:
                name = service.get('name')
                options = service.get('options', {})
                
                if not name:
                    errors.append("Service missing name")
                    continue
                
                if name not in Config.AVAILABLE_SERVICES:
                    errors.append(f"Unknown service: {name}")
                    continue
                
                try:
                    structure_manager.add_service(name, options)
                except Exception as e:
                    errors.append(f"Invalid service '{name}': {e}")
            
            # run structure validation
            structure_errors = structure_manager.validate_structure()
            errors.extend(structure_errors)
            
        except Exception as e:
            errors.append(f"Configuration error: {e}")
        
        return errors
    
    def _create_project_from_config(self, config):
        """Create project from configuration"""

        project_name = config.get('project_name')
        if not project_name:
            raise ValueError("Missing project name in configuration")
        
        structure_manager = self._create_project_structure_from_config(config)
        
        generator = DjangoProjectGenerator(structure_manager)
        generator.generate_project()
        
        self._print_success(f"Django project '{project_name}' created successfully!")
    
    def _create_project_structure_from_config(self, config, preview_only=False):
        """Create project structure from configuration"""
        project_name = config.get('project_name')
        
        structure_manager = ProjectStructureManager(project_name)
        
        core_config = config.get('core', {})
        core_location = core_config.get('location', Config.DEFAULT_PROJECT_STRUCTURE['core_location'])
        core_path = core_config.get('path', 'core')
        structure_manager.set_core_location(core_location, core_path)
        
        directories = config.get('directories', [])
        for directory in directories:
            name = directory.get('name')
            parent = directory.get('parent', "")
            structure_manager.add_directory(name, parent)
        
        apps = config.get('apps', [])
        for app in apps:
            name = app.get('name')
            directory = app.get('directory', "")
            structure_manager.add_app(name, directory)
        
        if not preview_only:
            services = config.get('services', [])
            for service in services:
                name = service.get('name')
                options = service.get('options', {})
                structure_manager.add_service(name, options)
        
        self.structure_manager = structure_manager
        
        return structure_manager
    
    def _print_welcome(self):
        """Print welcome message for interactive mode"""
        if self.console:
            self.console.print(Panel(
                "[bold green]Django Boilerplate Generator[/bold green]\n\n"
                "Create a fully customized Django project with flexible structure and services.",
                title="Welcome",
                expand=False
            ))
        else:
            print("Welcome to Django Boilerplate Generator")
            print("======================================")
            print()
    
    def _interactive_menu(self):
        """Show interactive menu for project configuration"""
        while True:
            self._print_menu()
            
            choice = self._get_menu_choice()
            
            if choice == 1:
                self._configure_core_location()
            elif choice == 2:
                self._manage_directories()
            elif choice == 3:
                self._manage_apps()
            elif choice == 4:
                self._manage_services()
            elif choice == 5:
                self._preview_structure()
            elif choice == 6:
                break
    
    def _print_menu(self):
        """Print the main interactive menu"""
        if self.console:
            self.console.print("\n[bold blue]Main Menu[/bold blue]")
            table = Table(show_header=False, expand=False)
            table.add_column("Option", style="cyan")
            table.add_column("Description")
            
            table.add_row("1", "Configure Core Location")
            table.add_row("2", "Manage Directories")
            table.add_row("3", "Manage Apps")
            table.add_row("4", "Manage Services")
            table.add_row("5", "Preview Project Structure")
            table.add_row("6", "Done")
            
            self.console.print(table)
        else:
            print("\nMain Menu:")
            print("1. Configure Core Location")
            print("2. Manage Directories")
            print("3. Manage Apps")
            print("4. Manage Services")
            print("5. Preview Project Structure")
            print("6. Done")
    
    def _get_menu_choice(self):
        """Get menu choice from user"""
        if self.console:
            return IntPrompt.ask("[bold cyan]Select an option[/bold cyan]", choices=["1", "2", "3", "4", "5", "6"])
        else:
            while True:
                try:
                    choice = int(input("Select an option (1-6): "))
                    if 1 <= choice <= 6:
                        return choice
                    print("Invalid choice. Please enter a number between 1 and 6.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
    
    def _configure_core_location(self):
        """Configure core location interactively"""
        if self.console:
            self.console.print("\n[bold blue]Configure Core Location[/bold blue]")
            
            options = ["root", "custom"]
            descriptions = [
                "Project root",
                "Custom path"
            ]
            
            table = Table(show_header=True)
            table.add_column("Option", style="cyan")
            table.add_column("Description")
            
            for i, (option, desc) in enumerate(zip(options, descriptions)):
                table.add_row(str(i+1), desc)
            
            self.console.print(table)
            
            choice = IntPrompt.ask(
                "[bold cyan]Select core location[/bold cyan]",
                choices=["1", "2"],
                default="2"
            )
            
            location_type = options[choice-1]
            
            core_path = "core"
            if location_type == "custom":
                core_path = Prompt.ask(
                    "[bold cyan]Enter custom path for core files[/bold cyan]",
                    default="core"
                )
            
            try:
                self.structure_manager.set_core_location(location_type, core_path)
                self.console.print("[green]Core location updated![/green]")
            except:
                self._print_error(
                    f"Directory {core_path} already exist."
                )
                return
        else:
            print("\nConfigure Core Location:")
            print("1. Project root")
            print("2. Custom path")
            
            while True:
                try:
                    choice = int(input("Select core location (1-2): "))
                    if 1 <= choice <= 2:
                        break
                    print("Invalid choice. Please enter a number between 1 and 2.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            
            options = ["root", "custom"]
            location_type = options[choice-1]
            
            core_path = "core"
            if location_type == "custom":
                core_path = input("Enter custom path for core files [core]: ") or "core"
            
            self.structure_manager.set_core_location(location_type, core_path)
            print("Core location updated!")
    
    def _manage_directories(self):
        """Manage directories interactively"""
        while True:
            if self.console:
                self.console.print("\n[bold blue]Manage Directories[/bold blue]")
                
                # Show existing directories
                self._show_directories()
                
                table = Table(show_header=False, expand=False)
                table.add_column("Option", style="cyan")
                table.add_column("Description")
                
                table.add_row("1", "Add Directory")
                table.add_row("2", "Back to Main Menu")
                
                self.console.print(table)
                
                choice = IntPrompt.ask(
                    "[bold cyan]Select an option[/bold cyan]",
                    choices=["1", "2"],
                    default="1"
                )
                
                if choice == 1:
                    self._add_directory_interactive()
                else:
                    break
            else:
                print("\nManage Directories:")
                self._show_directories()
                print("1. Add Directory")
                print("2. Back to Main Menu")
                
                while True:
                    try:
                        choice = int(input("Select an option (1-2): "))
                        if 1 <= choice <= 2:
                            break
                        print("Invalid choice. Please enter a number between 1 and 2.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
                
                if choice == 1:
                    self._add_directory_interactive()
                else:
                    break
    
    def _show_directories(self):
        """Show existing directories"""
        dirs = self.structure_manager.structure['directories']
        
        if not dirs:
            if self.console:
                self.console.print("[italic]No directories defined yet[/italic]")
            else:
                print("No directories defined yet")
            return
        
        if self.console:
            self.console.print("[bold]Existing Directories:[/bold]")
            self._show_directory_tree()
        else:
            print("Existing Directories:")
            for dir_path, info in dirs.items():
                print(f"  - {dir_path}")
    
    def _show_directory_tree(self):
        """Show directory tree using Rich"""
        if not self.console:
            return
        
        tree = Tree(f"📁 {self.structure_manager.project_name} (Root)")
        
        # get top-level directories
        top_dirs = {path: info for path, info in self.structure_manager.structure['directories'].items()
                   if not info['parent']}
        
        # get core path
        core_location = self.structure_manager.structure['core']['location']
        core_path = self.structure_manager.structure['core']['path']
        
        # add core node
        # TODO: must find a way to note the (Core) when custom
        core_node = tree.add(f"📁 {core_path} (Core)")
        
        # build directory tree
        for path, info in sorted(top_dirs.items()):
            dir_node = tree.add(f"📁 {info['name']}")
            self._add_subdirectories(dir_node, path)
        
        # show apps in their directories
        apps = self.structure_manager.structure['apps']
        root_apps = {name: path for name, path in apps.items() if '/' not in path}
        
        # show root apps
        for name, path in sorted(root_apps.items()):
            tree.add(f"🔸 {name} (App)")
        
        self.console.print(tree)
    
    def _preview_structure(self):
        """Show existing directories"""
        dirs = self.structure_manager.structure['directories']
        
        if self.console:
            self.console.print("[bold]Existing Directories:[/bold]")
            self._show_directory_tree()
        else:
            print("Existing Directories:")
            for dir_path, info in dirs.items():
                print(f"  - {dir_path}")

    def _add_subdirectories(self, parent_node, parent_path):
        """Recursively add subdirectories to tree"""
        dirs = self.structure_manager.structure['directories']
        apps = self.structure_manager.structure['apps']
        
        subdirs = {path: info for path, info in dirs.items()
                  if info['parent'] == parent_path}

        dir_apps = {name: path for name, path in apps.items()
                   if path.startswith(f"{parent_path}/") and '/' not in path[len(parent_path)+1:]}
        
        for path, info in sorted(subdirs.items()):
            dir_node = parent_node.add(f"📁 {info['name']}")
            self._add_subdirectories(dir_node, path)
        
        for name, path in sorted(dir_apps.items()):
            parent_node.add(f"🔸 {name} (App)")
    
    def _add_directory_interactive(self):
        """Add directory interactively"""
        if self.console:
            name = Prompt.ask("[bold cyan]Enter directory name[/bold cyan]")
            
            # show directory structure for parent selection
            self._show_directories()
            
            parent = Prompt.ask(
                "[bold cyan]Enter parent directory (leave empty for root)[/bold cyan]",
                default=""
            )
            
            try:
                path = self.structure_manager.add_directory(name, parent)
                self.console.print(f"[green]Directory '{path}' added![/green]")
            except Exception as e:
                self.console.print(f"[bold red]Error: {e}[/bold red]")
        else:
            name = input("Enter directory name: ")
            
            # show directory structure for parent selection
            self._show_directories()
            
            parent = input("Enter parent directory (leave empty for root): ") or ""
            
            try:
                path = self.structure_manager.add_directory(name, parent)
                print(f"Directory '{path}' added!")
            except Exception as e:
                print(f"Error: {e}")
    
    def _manage_apps(self):
        """Manage apps interactively"""
        while True:
            if self.console:
                self.console.print("\n[bold blue]Manage Apps[/bold blue]")
                
                # show existing apps in a table
                self._show_apps()
                
                table = Table(show_header=False, expand=False)
                table.add_column("Option", style="cyan")
                table.add_column("Description")
                
                table.add_row("1", "Add App")
                table.add_row("2", "Back to Main Menu")
                
                self.console.print(table)
                
                choice = IntPrompt.ask(
                    "[bold cyan]Select an option[/bold cyan]",
                    choices=["1", "2"],
                    default="1"
                )
                
                if choice == 1:
                    self._add_app_interactive()
                else:
                    break
            else:
                print("\nManage Apps:")
                self._show_apps()
                print("1. Add App")
                print("2. Back to Main Menu")
                
                while True:
                    try:
                        choice = int(input("Select an option (1-2): "))
                        if 1 <= choice <= 2:
                            break
                        print("Invalid choice. Please enter a number between 1 and 2.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
                
                if choice == 1:
                    self._add_app_interactive()
                else:
                    break
    
    def _show_apps(self):
        """Show existing apps"""
        apps = self.structure_manager.structure['apps']
        
        if not apps:
            if self.console:
                self.console.print("[italic]No apps defined yet[/italic]")
            else:
                print("No apps defined yet")
            return
        
        if self.console:
            table = Table(show_header=True)
            table.add_column("App Name", style="bold green")
            table.add_column("Path")
            
            for name, path in sorted(apps.items()):
                table.add_row(name, path)
            
            self.console.print("[bold]Existing Apps:[/bold]")
            self.console.print(table)
        else:
            print("Existing Apps:")
            for name, path in sorted(apps.items()):
                print(f"  - {name}: {path}")
    
    def _add_app_interactive(self):
        """Add app interactively"""
        if self.console:
            name = Prompt.ask("[bold cyan]Enter app name[/bold cyan]")
            
            # show directory structure for directory selection
            self._show_directories()
            
            directory = Prompt.ask(
                "[bold cyan]Enter directory for app (leave empty for root)[/bold cyan]",
                default=""
            )
            
            try:
                self.structure_manager.add_app(name, directory)
                self.console.print(f"[green]App '{name}' added![/green]")
            except Exception as e:
                self.console.print(f"[bold red]Error: {e}[/bold red]")
        else:
            name = input("Enter app name: ")
            
            # show directory structure for directory selection
            self._show_directories()
            
            directory = input("Enter directory for app (leave empty for root): ") or ""
            
            try:
                self.structure_manager.add_app(name, directory)
                print(f"App '{name}' added!")
            except Exception:
                print(f"Cannot add the app {name}")


if __name__ == "__main__":
    cli = DjangoBoilerplateCLI()
    cli.run()