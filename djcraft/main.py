#!/usr/bin/env python3
import sys

from cli.argument_parser import create_argument_parser
from cli.commands import (
    handle_create_command,
    handle_generate_from_config,
    handle_validate_command,
)
from cli.interactive import run_interactive_mode
from core.exceptions import DjCraftError 

try:
    from rich.console import Console
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class DjCraftCli:
    """
    Command Line Interface for Django Boilerplate Generator
    """
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.structure_manager = None

    def run(self):
        """Main entry point for CLI"""
        parser = create_argument_parser()
        args = parser.parse_args()

        try:
            if args.command == 'create':
                handle_create_command(args)
            elif args.command == 'interactive':
                if not RICH_AVAILABLE:
                    print("Rich library is required for interactive mode.")
                    print("Install it with: pip install rich")
                    sys.exit(1)
                run_interactive_mode(self.console)
            elif args.command == 'generate':
                handle_generate_from_config(args.config_file)
            elif args.command == 'validate':
                handle_validate_command(args.config_file, self.console, RICH_AVAILABLE)
            else:
                parser.print_help()
        except DjCraftError as e:
            self._print_error(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            self._print_error(f"Unexpected error: {e}")
            if args.command == 'interactive':
                import traceback
                traceback.print_exc()
            sys.exit(1)

    def _print_error(self, message):
        """Print error message with formatting if available"""
        if self.console:
            self.console.print(f"[bold red]{message}[/bold red]")
        else:
            print(f"Error: {message}")

    def _print_success(self, message):
        """Print success message with formatting if available"""
        if self.console:
            self.console.print(f"[bold green]{message}[/bold green]")
        else:
            print(f"Success: {message}")


if __name__ == "__main__":
    cli = DjCraftCli()
    cli.run()
