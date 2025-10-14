from typing import Any, Dict, Tuple

from core.configuration_manager import ConfigurationManager
from core.project_structure_manager import ProjectStructureManager
from rich.console import Console
from rich.prompt import IntPrompt, Prompt
from rich.table import Table


def ask_core_location(console: Console) -> Tuple[str, str]:
    """Prompts the user for the core Django files location."""
    options = ["root", "custom"]
    descriptions = [
        "Project root",
        "Custom path"
    ]

    table = Table(show_header=True, show_lines=False)
    table.add_column("Option", style="cyan")
    table.add_column("Description")

    for i, (option, desc) in enumerate(zip(options, descriptions)):
        table.add_row(str(i+1), desc)

    console.print(table)

    choice = IntPrompt.ask(
        "[bold cyan]Select core location[/bold cyan]",
        choices=[str(i+1) for i in range(len(options))],
        default="2",
        console=console
    )

    location_type = options[int(choice) - 1]
    core_path = "core"  # Default path for custom location

    if location_type == "custom":
        core_path = Prompt.ask(
            "[bold cyan]Enter custom path for core files[/bold cyan]",
            default="core",
            console=console
        )

    return location_type, core_path


def ask_directory_details(structure_manager: ProjectStructureManager, console: Console) -> Tuple[str, str]:
    """Prompts the user for directory name and parent."""
    name = Prompt.ask("[bold cyan]Enter directory name[/bold cyan]", console=console)

    parent = Prompt.ask(
        "[bold cyan]Enter parent directory (leave empty for root)[/bold cyan]",
        default="",
        console=console
    )
    # Show existing directories to help with parent selection
    show_directories(structure_manager, console)
    return name, parent


def ask_app_details(structure_manager: ProjectStructureManager, console: Console) -> Tuple[str, str]:
    """Prompts the user for app name and directory."""
    name = Prompt.ask("[bold cyan]Enter app name[/bold cyan]", console=console)

    directory = Prompt.ask(
        "[bold cyan]Enter directory for app (leave empty for root)[/bold cyan]",
        default="",
        console=console
    )
    # Show existing directories to help with app placement
    show_directories(structure_manager, console)
    return name, directory


def ask_service_to_add(console: Console) -> str | None:
    """Prompts the user to select a service to add."""
    available_services = list(ConfigurationManager().get_available_services())
    if not available_services:
        console.print("[italic]No services available to add.[/italic]")
        return None

    console.print("\n[bold blue]Available Services:[/bold blue]")

    table = Table(show_header=True, show_lines=False)
    table.add_column("Option", style="cyan")
    table.add_column("Service Name")
    table.add_column("Description")

    for i, service_name in enumerate(available_services):
        info = ConfigurationManager().get_service_info(service_name)
        table.add_row(str(i + 1), service_name, info['description'])

    console.print(table)

    while True:
        try:
            choice = IntPrompt.ask(
                "[bold cyan]Select a service to add[/bold cyan]",
                choices=[str(i + 1) for i in range(len(available_services))],
                console=console
            )
            service_name = available_services[choice - 1]
            return service_name
        except (ValueError, IndexError):
            console.print("[bold red]Invalid choice. Please select a valid option.[/bold red]")


def ask_service_options(service_name: str, service_info: Dict[str, Any], console: Console) -> Dict[str, Any]:
    """Prompts the user for options for a specific service."""
    options = {}
    if service_info.get('options'):
        console.print(f"\n[bold blue]Configure options for {service_name}:[/bold blue]")
        for option_name, allowed_values in service_info['options'].items():
            if isinstance(allowed_values, list):
                options_table = Table(show_header=True, show_lines=False)
                options_table.add_column("Option", style="cyan")
                options_table.add_column("Value")

                for i, value in enumerate(allowed_values):
                    options_table.add_row(str(i+1), str(value))

                console.print(options_table)

                while True:
                    try:
                        default_value = service_info['default_options'].get(option_name)
                        default_idx = -1
                        if default_value in allowed_values:
                             default_idx = allowed_values.index(default_value)

                        option_choice_str = Prompt.ask(
                            f"[bold cyan]Select value for '{option_name}'[/bold cyan]",
                            choices=[str(i + 1) for i in range(len(allowed_values))],
                            default=str(default_idx + 1) if default_idx != -1 else "1",
                            console=console
                        )
                        option_choice = int(option_choice_str)
                        if 1 <= option_choice <= len(allowed_values):
                            options[option_name] = allowed_values[option_choice - 1]
                            break
                        else:
                            console.print("[bold red]Invalid choice. Please select a valid option.[/bold red]")
                    except (ValueError, IndexError):
                        console.print("[bold red]Invalid input. Please enter a number.[/bold red]")
            else:
                 default_value = service_info['default_options'].get(option_name, "")
                 options[option_name] = Prompt.ask(
                     f"[bold cyan]Enter value for '{option_name}'[/bold cyan]",
                     default=str(default_value),
                     console=console
                 )
    return options


# to avoid circular dependency issues
from .ui import show_directories  # noqa: E402
