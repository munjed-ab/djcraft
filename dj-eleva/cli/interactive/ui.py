from pathlib import Path

from core.project_structure_manager import ProjectStructureManager
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree


def print_welcome(console: Console):
    """Prints the welcome message for interactive mode."""
    console.print(Panel(
        "[bold green]Django Boilerplate Generator[/bold green]\n\n"
        "Create a fully customized Django project with flexible structure and services.",
        title="Welcome",
        expand=False
    ))


def print_menu(console: Console):
    """Prints the main interactive menu."""
    console.print("\n[bold blue]Main Menu[/bold blue]")
    table = Table(show_header=False, expand=False, show_lines=False)
    table.add_column("Option", style="cyan")
    table.add_column("Description")

    table.add_row("1", "Configure Core Location")
    table.add_row("2", "Manage Directories")
    table.add_row("3", "Manage Apps")
    table.add_row("4", "Manage Services")
    table.add_row("5", "Preview Project Structure")
    table.add_row("6", "Done")

    console.print(table)


def show_directories(structure_manager: ProjectStructureManager, console: Console):
    """Shows existing directories using a tree structure."""
    dirs = structure_manager.structure['directories']

    if not dirs:
        console.print("[italic]No directories defined yet[/italic]")
        return

    console.print("[bold]Existing Directories:[/bold]")
    _show_directory_tree(structure_manager, console)


def show_apps(structure_manager: ProjectStructureManager, console: Console):
    """Shows existing apps in a table."""
    apps = structure_manager.structure['apps']

    if not apps:
        console.print("[italic]No apps defined yet[/italic]")
        return

    table = Table(show_header=True, show_lines=False)
    table.add_column("App Name", style="bold green")
    table.add_column("Path")

    for name, path in sorted(apps.items()):
        table.add_row(name, path)

    console.print("[bold]Existing Apps:[/bold]")
    console.print(table)


def show_services(structure_manager: ProjectStructureManager, console: Console):
    """Shows existing services in a table."""
    services = structure_manager.structure['services']

    if not services:
        console.print("[italic]No services added yet[/italic]")
        return

    table = Table(show_header=True, show_lines=False)
    table.add_column("Service Name", style="bold green")
    table.add_column("Options")

    for service in services:
        name = service['name']
        options = service['options']
        # Use a simple string representation for options in the table
        options_str = str(options) if options else "None"
        table.add_row(name, options_str)

    console.print("[bold]Existing Services:[/bold]")
    console.print(table)


def preview_structure(structure_manager: ProjectStructureManager, console: Console):
    """Shows a preview of the project structure using a tree."""
    console.print("\n[bold blue]Project Structure Preview:[/bold blue]")
    _show_directory_tree(structure_manager, console)


def _show_directory_tree(structure_manager: ProjectStructureManager, console: Console):
    """Helper function to build and print the directory tree."""
    project_name = structure_manager.project_name
    structure = structure_manager.structure
    core_path_str = structure['core']['path']

    tree = Tree(f"📂 [bold blue]{project_name}[/bold blue] (Root)")

    # Dictionary to hold tree nodes for easier adding of children
    directory_nodes = {"": tree}  # Root directory maps to the main tree

    # Add top-level directories and their contents
    top_level_items = sorted([
        (path, info) for path, info in structure['directories'].items() if not info['parent']
    ])

    # Include root-level apps and core if they are at the root
    root_level_apps = sorted([
        (name, path) for name, path in structure['apps'].items() if '/' not in path and path != core_path_str
    ])


    # Combine top-level directories and root-level apps/core for iteration
    all_root_items = sorted(list(top_level_items) + list(root_level_apps))

    if structure['core']['location'] == 'root':
         all_root_items.append((core_path_str, {'type': 'core'})) # Add core as a special item

    for item_path, item_info in all_root_items:
        if isinstance(item_info, dict) and item_info.get('type') == 'core':
             # Handle the core location if it's at the root
            core_label = f"⚙️ [bold yellow] {Path(item_path).name}[/bold yellow] ([italic]Core[/italic])"
            tree.add(core_label)
        elif isinstance(item_info, dict) and 'name' in item_info: # It's a directory
            dir_node = tree.add(f"📁 [bold blue]{item_info['name']}[/bold blue]")
            directory_nodes[item_path] = dir_node
            _add_sub_items_to_tree(structure_manager, dir_node, item_path, directory_nodes)
        else: # It's a root-level app not at the core path
             app_name = item_path # In root_level_apps, item_path is the app name
             tree.add(f"📦 [bold green]{app_name}[/bold green] (App)")


    console.print(tree)


def _add_sub_items_to_tree(structure_manager: ProjectStructureManager, parent_node: Tree, parent_path: str, directory_nodes):
    """Recursively adds subdirectories, apps, and core (if applicable) to a Rich tree node."""
    structure = structure_manager.structure
    core_path_str = structure['core']['path']

    # Add subdirectories within this parent directory
    subdirs = sorted([
        (path, info) for path, info in structure['directories'].items() if info.get('parent') == parent_path
    ])

    for subdir_path, subdir_info in subdirs:
        # Don't add the core path again if it's a subdirectory already handled
        if subdir_path != core_path_str:
            dir_node = parent_node.add(f"📁 [bold blue]{subdir_info['name']}[/bold blue]")
            directory_nodes[subdir_path] = dir_node  # Store the node
            _add_sub_items_to_tree(structure_manager, dir_node, subdir_path, directory_nodes)


    # Add apps directly within this parent directory
    dir_apps = sorted([
        (name, path) for name, path in structure['apps'].items()
        if str(Path(path).parent) == parent_path and path != core_path_str # Exclude apps at core path
    ])

    for app_name, app_path in dir_apps:
        parent_node.add(f"📦 [bold green]{app_name}[/bold green] (App)")

    # Check if the core path is directly within this parent directory and add it
    if core_path_str != "" and str(Path(core_path_str).parent) == parent_path:
        core_name = Path(core_path_str).name
        core_label = f"⚙️ [bold yellow] {core_name}[/bold yellow] ([italic]Core[/italic])"
        parent_node.add(core_label)