from core.configuration_manager import ConfigurationManager
from core.exceptions import DjangoBoilerplateError
from core.project_structure_manager import ProjectStructureManager
from rich.console import Console
from rich.prompt import IntPrompt
from rich.table import Table

from .prompts import (
    ask_app_details,
    ask_core_location,
    ask_directory_details,
    ask_service_options,
    ask_service_to_add,
)
from .ui import (
    preview_structure,
    print_menu,
    show_apps,
    show_directories,
    show_services,
)


def interactive_menu(structure_manager: ProjectStructureManager, console: Console):
    """
    Runs the main interactive configuration menu.

    Args:
        structure_manager: The ProjectStructureManager instance.
        console: The Rich Console instance.
    """
    while True:
        print_menu(console)
        choice = _get_menu_choice(console)

        if choice == 1:
            _configure_core_location(structure_manager, console)
        elif choice == 2:
            _manage_directories(structure_manager, console)
        elif choice == 3:
            _manage_apps(structure_manager, console)
        elif choice == 4:
            _manage_services(structure_manager, console)
        elif choice == 5:
            preview_structure(structure_manager, console)
        elif choice == 6:
            break


def _get_menu_choice(console: Console) -> int:
    """Gets the user's menu choice."""
    return IntPrompt.ask("[bold cyan]Select an option[/bold cyan]", choices=["1", "2", "3", "4", "5", "6"], console=console)


def _configure_core_location(structure_manager: ProjectStructureManager, console: Console):
    """Handles the configuration of the core Django files location."""
    console.print("\n[bold blue]Configure Core Location[/bold blue]")
    location_type, core_path = ask_core_location(console)

    try:
        structure_manager.set_core_location(location_type, core_path)
        console.print("[green]Core location updated![/green]")
    except DjangoBoilerplateError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")


def _manage_directories(structure_manager: ProjectStructureManager, console: Console):
    """Manages the adding of directories."""
    while True:
        console.print("\n[bold blue]Manage Directories[/bold blue]")
        show_directories(structure_manager, console)

        table = Table(show_header=False, expand=False, show_lines=False)
        table.add_column("Option", style="cyan")
        table.add_column("Description")
        table.add_row("1", "Add Directory")
        table.add_row("2", "Back to Main Menu")
        console.print(table)

        choice = IntPrompt.ask("[bold cyan]Select an option[/bold cyan]", choices=["1", "2"], default="1", console=console)

        if choice == 1:
            _add_directory_interactive(structure_manager, console)
        else:
            break


def _add_directory_interactive(structure_manager: ProjectStructureManager, console: Console):
    """Adds a directory based on user input."""
    name, parent = ask_directory_details(structure_manager, console)
    try:
        path = structure_manager.add_directory(name, parent)
        console.print(f"[green]Directory '{path}' added![/green]")
    except DjangoBoilerplateError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")


def _manage_apps(structure_manager: ProjectStructureManager, console: Console):
    """Manages the adding of apps."""
    while True:
        console.print("\n[bold blue]Manage Apps[/bold blue]")
        show_apps(structure_manager, console)

        table = Table(show_header=False, expand=False, show_lines=False)
        table.add_column("Option", style="cyan")
        table.add_column("Description")
        table.add_row("1", "Add App")
        table.add_row("2", "Back to Main Menu")
        console.print(table)

        choice = IntPrompt.ask("[bold cyan]Select an option[/bold cyan]", choices=["1", "2"], default="1", console=console)

        if choice == 1:
            _add_app_interactive(structure_manager, console)
        else:
            break


def _add_app_interactive(structure_manager: ProjectStructureManager, console: Console):
    """Adds an app based on user input."""
    name, directory = ask_app_details(structure_manager, console)
    try:
        structure_manager.add_app(name, directory)
        console.print(f"[green]App '{name}' added![/green]")
    except DjangoBoilerplateError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")


def _manage_services(structure_manager: ProjectStructureManager, console: Console):
    """Manages the adding of services."""
    while True:
        console.print("\n[bold blue]Manage Services[/bold blue]")
        show_services(structure_manager, console)

        table = Table(show_header=False, expand=False, show_lines=False)
        table.add_column("Option", style="cyan")
        table.add_column("Description")
        table.add_row("1", "Add Service")
        table.add_row("2", "Back to Main Menu")
        console.print(table)

        choice = IntPrompt.ask("[bold cyan]Select an option[/bold cyan]", choices=["1", "2"], default="1", console=console)

        if choice == 1:
            _add_service_interactive(structure_manager, console)
        else:
            break


def _add_service_interactive(structure_manager: ProjectStructureManager, console: Console):
    """Adds a service based on user input."""
    service_name = ask_service_to_add(console)
    if not service_name:
        return

    service_info = ConfigurationManager().get_service_info(service_name)
    options = {}
    if service_info.get('options'):
         options = ask_service_options(service_name, service_info, console)

    try:
        structure_manager.add_service(service_name, options)
        console.print(f"[green]Service '{service_name}' added![/green]")
    except DjangoBoilerplateError as e:
        console.print(f"[bold red]Error adding service: {e}[/bold red]")