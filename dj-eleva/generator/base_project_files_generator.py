# generator/base_project_files_generator.py

from core.project_structure_manager import ProjectStructureManager

from .abstract_generator import AbstractGenerator
from .file_renderer import FileRenderer
from .requirements_manager import RequirementsManager


class BaseProjectFilesGenerator(AbstractGenerator):
    """Generates base project files like manage.py, README.md, .gitignore, etc."""

    def __init__(self, structure_manager: ProjectStructureManager, 
                 file_renderer: FileRenderer, 
                 requirements_manager: RequirementsManager,
                 config = None):
        """
        Initialize the BaseProjectFilesGenerator.

        Args:
            structure_manager: The ProjectStructureManager instance.
            file_renderer: The FileRenderer instance for rendering templates.
            requirements_manager: The RequirementsManager instance.
            config: Optional configuration dictionary.
        """
        super().__init__(structure_manager, file_renderer, requirements_manager, config)

    def create_directories(self) -> None:
        """Create necessary directories for base project files."""
        # Base directories are created by the structure manager
        pass
        
    def generate_files(self) -> None:
        """Generate the base project files."""
        self._generate_manage_py()
        self._generate_gitignore()
        self._generate_readme()
        # Requirements are handled separately by RequirementsManager after all generators run

    def _generate_manage_py(self) -> None:
        """Generate the manage.py file."""
        core_import_path = str(self.structure_manager.get_core_path_str()).replace('/', '.')
        manage_py_path = self.project_path / 'manage.py'
        self.file_renderer.render_template(
            'project_template/manage.py.template',
            manage_py_path,
            {'core_path': core_import_path}
        )
        # Make manage.py executable
        if manage_py_path.exists():
            manage_py_path.chmod(manage_py_path.stat().st_mode | 0o111)

    def _generate_gitignore(self) -> None:
        """Generate the .gitignore file."""
        self.file_renderer.render_template(
            'project_template/.gitignore.template',
            self.project_path / '.gitignore'
        )

    def _generate_readme(self) -> None:
        """Generate the README.md file."""
        services = [s['name'] for s in self.structure_manager.get_services()]
        context = {
            'project_name': self.project_name,
            'apps': list(self.structure_manager.structure['apps'].keys()),
            'use_docker': 'docker' in services,
            'use_celery': 'celery' in services,
            'use_redis': 'redis' in services,
            'use_rest_api': 'rest_api' in services,
            'core_location': self.structure_manager.get_core_location()
        }
        self.file_renderer.render_template(
            'project_template/README.md.template',
            self.project_path / 'README.md',
            context
        )