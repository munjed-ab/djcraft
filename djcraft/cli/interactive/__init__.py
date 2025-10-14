import sys

from core.config import DefaultSettings
from core.exceptions import DjCraftError 
from core.project_structure_manager import ProjectStructureManager
from generator.generator import (
    DjangoProjectGenerator,
)
from rich.console import Console
from rich.prompt import Confirm, Prompt

from ..config_io import save_configuration
from .menu import interactive_menu
from .ui import preview_structure, print_welcome


def run_interactive_mode(console: Console) -> ProjectStructureManager:
    """
    Run interactive project creation mode.

    Args:
        console: Rich console.

    Returns:
        ProjectStructureManager: Configured structure manager.
    """
    print_welcome(console)

    project_name = Prompt.ask(
        "[bold blue]Enter project name[/bold blue]",
        default=DefaultSettings.CLI_DEFAULTS.project_name,
        console=console
    )

    try:
        structure_manager = ProjectStructureManager(project_name)

        interactive_menu(structure_manager, console)

        if Confirm.ask("[bold green]Generate project now?[/bold green]", console=console):
            preview_structure(structure_manager, console)

            if Confirm.ask("[bold green]Proceed with generation?[/bold green]", console=console):
                generator = DjangoProjectGenerator(structure_manager)
                generator.generate()
                console.print(f"[bold green]Django project '{project_name}' created successfully![/bold green]")

        if Confirm.ask("[bold blue]Save configuration to file?[/bold blue]", console=console):
            config_path = Prompt.ask(
                "[bold blue]Enter file path to save configuration[/bold blue]",
                default=f"{project_name}_config.yaml",
                console=console
            )
            try:
                save_configuration(structure_manager, config_path)
                console.print(f"[bold green]Configuration successfully saved to {config_path}[/bold green]")
            except Exception as e:
                console.print(f"[bold red]Failed to save configuration: {e}[/bold red]")


        return structure_manager

    except DjCraftError as e:
        console.print(f"[bold red]Error during interactive mode: {e}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during interactive mode: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
