# generator/generator_factory.py
from typing import Dict, Type

from core.project_structure_manager import ProjectStructureManager

from .abstract_generator import AbstractGenerator
from .app_generator import AppGenerator
from .base_project_files_generator import BaseProjectFilesGenerator
from .core_file_generator import CoreFileGenerator
from .file_renderer import FileRenderer
from .requirements_manager import RequirementsManager
from .service_generator import ServiceGenerator


class GeneratorFactory:
    """Factory class for creating different types of generators."""

    _generator_registry: Dict[str, Type[AbstractGenerator]] = {}

    @classmethod
    def register_generator(cls, generator_type: str, generator_class: Type[AbstractGenerator]) -> None:
        """Register a generator class with a specific type."""
        cls._generator_registry[generator_type] = generator_class

    @classmethod
    def create_generator(cls, generator_type: str, 
                        structure_manager: ProjectStructureManager,
                        file_renderer: FileRenderer,
                        requirements_manager: RequirementsManager,
                        config = None) -> AbstractGenerator:
        """Create a generator instance based on the specified type."""
        if generator_type not in cls._generator_registry:
            raise ValueError(f"Unknown generator type: {generator_type}")
        
        generator_class = cls._generator_registry[generator_type]
        return generator_class(structure_manager, file_renderer, requirements_manager, config)

    @classmethod
    def create_all_generators(cls, 
                            structure_manager: ProjectStructureManager,
                            file_renderer: FileRenderer,
                            requirements_manager: RequirementsManager,
                            config) -> Dict[str, AbstractGenerator]:
        """Create all required generators based on the project configuration."""
        generators = {}
        config = config.get_all_config()
        # Always create base, core files generator
        generators['base_files'] = BaseProjectFilesGenerator(structure_manager, file_renderer, requirements_manager, config)
        generators['core_files'] = CoreFileGenerator(structure_manager, file_renderer, requirements_manager, config)

        # Create app generator if apps are defined
        if config.get('apps'):
            generators['apps'] = AppGenerator(structure_manager, file_renderer, requirements_manager, config)
        
        # Create service generator if services are defined
        if config.get('services'):
            generators['services'] = ServiceGenerator(structure_manager, file_renderer, requirements_manager)

            
        
        # Create additional generators based on configuration
        for generator_type in cls._generator_registry:
            if generator_type not in generators and config.get(generator_type):
                generators[generator_type] = cls.create_generator(
                    generator_type, structure_manager, file_renderer, requirements_manager, config
                )
        
        return generators


GeneratorFactory.register_generator('base_files', BaseProjectFilesGenerator)
GeneratorFactory.register_generator('core_files', CoreFileGenerator)
GeneratorFactory.register_generator('apps', AppGenerator)
GeneratorFactory.register_generator('services', ServiceGenerator)