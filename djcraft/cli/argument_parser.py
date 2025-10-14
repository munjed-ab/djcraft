import argparse
import json

from core.config import DefaultSettings


def create_argument_parser():
    parser = argparse.ArgumentParser(
        description='Django Project Boilerplate Generator',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    _add_create_command(subparsers)
    _add_interactive_command(subparsers)
    _add_generate_command(subparsers)
    _add_validate_command(subparsers)

    return parser


def _add_create_command(subparsers):
    """Add 'create' command parser"""

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
        default=DefaultSettings.PROJECT_STRUCTURE.core_location,
        help='Location of core configuration'
    )
    create_parser.add_argument(
        '--core-path',
        help='Custom path for core files (when --core-location=custom)'
    )
    create_parser.add_argument(
        '--services',
        nargs='+',
        choices=DefaultSettings.AVAILABLE_SERVICES.get_service_names(),
        default=[],
        help='Services to include in the project'
    )
    create_parser.add_argument(
        '--service-options',
        type=json.loads,
        default={},
        help='JSON string with service options'
    )


def _add_interactive_command(subparsers):
    """Add 'interactive' command parser"""
    subparsers.add_parser(
        'interactive',
        help='Create a project in interactive mode'
    )


def _add_generate_command(subparsers):
    """Add 'generate' command parser"""
    generate_parser = subparsers.add_parser(
        'generate',
        help='Generate project from config file'
    )
    generate_parser.add_argument(
        'config_file',
        help='Path to YAML or JSON configuration file'
    )


def _add_validate_command(subparsers):
    """Add 'validate' command parser"""
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate project configuration file without generating'
    )
    validate_parser.add_argument(
        'config_file',
        help='Path to YAML or JSON configuration file to validate'
    )
