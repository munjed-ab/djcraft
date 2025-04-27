# generator/base_generator.py


from .file_renderer import FileRenderer
from .generator_factory import GeneratorFactory
from .requirements_manager import RequirementsManager
from core.configuration_manager import ConfigurationManager

class DjangoProjectGenerator:
    """Generates the Django project structure and files using Factory and Template Method patterns."""

    def __init__(self, structure_manager, config = None):
        """
        Initialize the DjangoProjectGenerator.

        Args:
            project_name: The name of the Django project.
            project_path: The root path for the new project.
            config: A dictionary containing the project configuration.
        """
        self.config = config or ConfigurationManager()

        # Initialize core componentsself.structure_manager
        self.structure_manager = structure_manager
        self.file_renderer = FileRenderer("templates")
        self.requirements_manager = RequirementsManager(self.structure_manager.project_path)
        
        # Use factory to create all required generators
        self.generators = GeneratorFactory.create_all_generators(
            self.structure_manager,
            self.file_renderer,
            self.requirements_manager,
            self.config
        )

    def generate(self) -> None:
        """Generate the entire Django project using the Template Method pattern."""
        print(f"Generating Django project '{self.structure_manager.project_name}' at {self.structure_manager.project_path}...")

        # 1. Create base project structure
        # self.structure_manager.create_base_structure()

        # 2. Generate all other components using registered generators
        for generator_name, generator in self.generators.items():
            print(f"Generating {generator_name}...")
            generator.generate()

        # 4. Finalize requirements
        # self.requirements_manager.finalize_requirements()

        print("Project generation complete.")

    # All generation methods have been moved to specialized generator classes
    # using the Template Method pattern and Factory pattern for better organization
    # and extensibility.
