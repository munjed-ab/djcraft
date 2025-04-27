from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from core.configuration_manager import ConfigurationManager
from core.project_structure_manager import ProjectStructureManager

from .abstract_generator import AbstractGenerator
from .file_renderer import FileRenderer
from .requirements_manager import RequirementsManager


# Strategy Pattern: Different app type strategies
class AppTypeStrategy(Protocol):
    """Strategy interface for different app types"""
    def generate_app_files(self, app_name: str, app_dir: Path, app_import_path: str, 
                          file_renderer: FileRenderer, template_base_dir: str) -> None:
        """Generate app-specific files based on app type"""
        pass


class StandardAppStrategy:
    """Strategy for standard Django apps"""
    def generate_app_files(self, app_name: str, app_dir: Path, app_import_path: str,
                          file_renderer: FileRenderer, template_base_dir: str) -> None:
        config = ConfigurationManager()
        config = config.get_all_config()
        if 'app' in config['files']:
            for file_name in config['files']['app']:
                template_name = f'{template_base_dir}/{file_name}.template'
                context = {
                    'app_name': app_name,
                    'app_import_path': app_import_path,
                }
                file_renderer.render_template(template_name, app_dir / file_name, context)


class ApiAppStrategy:
    """Strategy for REST API apps"""
    def generate_app_files(self, app_name: str, app_dir: Path, app_import_path: str,
                          file_renderer: FileRenderer, template_base_dir: str) -> None:
        # Generate standard files first
        StandardAppStrategy().generate_app_files(app_name, app_dir, app_import_path, file_renderer, template_base_dir)
        config = ConfigurationManager()
        config = config.get_all_config()
        # Add API-specific files
        if 'rest_api' in config['files']:
            for file_name in config['files']['rest_api']:
                template_name = f'{template_base_dir}/api/{file_name}.template'
                context = {
                    'app_name': app_name,
                    'app_import_path': app_import_path,
                }
                file_renderer.render_template(template_name, app_dir / file_name, context)
            
            # Create serializers.py for API apps
            template_name = f'{template_base_dir}/api/serializers.py.template'
            file_renderer.render_template(template_name, app_dir / 'serializers.py', {
                'app_name': app_name,
                'app_import_path': app_import_path,
            })


class AuthAppStrategy:
    """Strategy for authentication apps"""
    def generate_app_files(self, app_name: str, app_dir: Path, app_import_path: str,
                          file_renderer: FileRenderer, template_base_dir: str) -> None:
        config = ConfigurationManager()
        config = config.get_all_config()
        if 'auth' in config['files']:
            for file_name in config['files']['auth']:
                if '/' not in file_name:  # Skip subdirectory files, they're handled separately
                    template_name = f'{template_base_dir}/auth/{file_name}.template'
                    context = {
                        'app_name': app_name,
                        'app_import_path': app_import_path,
                    }
                    file_renderer.render_template(template_name, app_dir / file_name, context)


# Decorator Pattern: App Feature Decorators
class AppFeatureDecorator(ABC):
    """Base decorator for app features"""
    def __init__(self, app_dir: Path, file_renderer: FileRenderer, template_base_dir: str):
        self.app_dir = app_dir
        self.file_renderer = file_renderer
        self.template_base_dir = template_base_dir
    
    @abstractmethod
    def add_feature(self, app_name: str, app_import_path: str) -> None:
        """Add a feature to the app"""
        pass


class ModelViewsDecorator(AppFeatureDecorator):
    """Decorator for adding model-based views"""
    def add_feature(self, app_name: str, app_import_path: str) -> None:
        template_name = f'{self.template_base_dir}/features/model_views.py.template'
        self.file_renderer.render_template(
            template_name,
            self.app_dir / 'model_views.py',
            {'app_name': app_name, 'app_import_path': app_import_path}
        )


class FormDecorator(AppFeatureDecorator):
    """Decorator for adding forms"""
    def add_feature(self, app_name: str, app_import_path: str) -> None:
        template_name = f'{self.template_base_dir}/features/forms.py.template'
        self.file_renderer.render_template(
            template_name,
            self.app_dir / 'forms.py',
            {'app_name': app_name, 'app_import_path': app_import_path}
        )


class SignalsDecorator(AppFeatureDecorator):
    """Decorator for adding signals"""
    def add_feature(self, app_name: str, app_import_path: str) -> None:
        template_name = f'{self.template_base_dir}/features/signals.py.template'
        self.file_renderer.render_template(
            template_name,
            self.app_dir / 'signals.py',
            {'app_name': app_name, 'app_import_path': app_import_path}
        )


# Builder Pattern: App Builder
class AppBuilder:
    """Builder for constructing Django apps with various configurations"""
    def __init__(self, app_name: str, app_dir: Path, app_import_path: str,
                file_renderer: FileRenderer, template_base_dir: str):
        self.app_name = app_name
        self.app_dir = app_dir
        self.app_import_path = app_import_path
        self.file_renderer = file_renderer
        self.template_base_dir = template_base_dir
        self.strategy: Optional[AppTypeStrategy] = None
        self.decorators: List[AppFeatureDecorator] = []
    
    def with_strategy(self, strategy: AppTypeStrategy) -> 'AppBuilder':
        """Set the app type strategy"""
        self.strategy = strategy
        return self
    
    def with_feature(self, decorator: AppFeatureDecorator) -> 'AppBuilder':
        """Add a feature decorator"""
        self.decorators.append(decorator)
        return self
    
    def build(self) -> None:
        """Build the app with the configured strategy and features"""
        if self.strategy:
            self.strategy.generate_app_files(
                self.app_name, self.app_dir, self.app_import_path,
                self.file_renderer, self.template_base_dir
            )
        
        # Apply all decorators
        for decorator in self.decorators:
            decorator.add_feature(self.app_name, self.app_import_path)


class AppGenerator(AbstractGenerator):
    """
    Generates individual Django app directories and files using Template Method pattern.
    """
    def __init__(self, structure_manager: ProjectStructureManager, 
                 file_renderer: FileRenderer,
                 requirements_manager: RequirementsManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AppGenerator.

        Args:
            structure_manager: The ProjectStructureManager instance.
            file_renderer: The FileRenderer instance for rendering templates.
            requirements_manager: The RequirementsManager instance.
            config: Optional configuration dictionary.
        """
        super().__init__(structure_manager, file_renderer, requirements_manager, config)
        self.template_base_dir = 'app_template'

    def create_directories(self) -> None:
        """
        Create necessary directories for all apps defined in the project structure.
        """
        apps = self.structure_manager.structure.get('apps', {})
        
        for app_name, app_path_str in apps.items():
            app_dir = self.project_path / app_path_str
            app_dir.mkdir(parents=True, exist_ok=True)
            
            # Create migrations directory
            migrations_dir = app_dir / 'migrations'
            migrations_dir.mkdir(exist_ok=True)
            (migrations_dir / '__init__.py').touch()
            
            # Create tests directory
            tests_dir = app_dir / 'tests'
            tests_dir.mkdir(exist_ok=True)
            (tests_dir / '__init__.py').touch()
    
    def generate_files(self) -> None:
        """
        Generate all app files for apps defined in the project structure.
        """
        apps = self.structure_manager.structure.get('apps', {})
        
        for app_name, app_path_str in apps.items():
            app_dir = self.project_path / app_path_str
            self._generate_standard_app_files(app_name, app_dir, app_path_str)

    def _generate_standard_app_files(self, app_name: str, app_dir: Path, app_path_str: str) -> None:
        """
        Generates the standard Python files for a Django app using the Builder pattern.

        Args:
            app_name: The name of the app.
            app_dir: The Path object for the app's directory.
            app_path_str: The string representation of the app's path relative to the project root.
        """
        # Get the Python import path for this specific app
        app_import_path = app_path_str.replace('/', '.')
        
        # Determine app type based on configuration or naming conventions
        app_type = self._determine_app_type(app_name)
        
        # Create app builder
        builder = AppBuilder(
            app_name=app_name,
            app_dir=app_dir,
            app_import_path=app_import_path,
            file_renderer=self.file_renderer,
            template_base_dir=self.template_base_dir
        )
        
        # Configure builder based on app type
        if app_type == 'api':
            builder.with_strategy(ApiAppStrategy())
        elif app_type == 'auth':
            builder.with_strategy(AuthAppStrategy())
        else:  # Default to standard app
            builder.with_strategy(StandardAppStrategy())
        
        # Add optional features based on configuration
        if self._should_add_feature(app_name, 'forms'):
            builder.with_feature(FormDecorator(app_dir, self.file_renderer, self.template_base_dir))
        
        if self._should_add_feature(app_name, 'signals'):
            builder.with_feature(SignalsDecorator(app_dir, self.file_renderer, self.template_base_dir))
        
        if self._should_add_feature(app_name, 'model_views'):
            builder.with_feature(ModelViewsDecorator(app_dir, self.file_renderer, self.template_base_dir))
        
        # Build the app
        builder.build()


    def _generate_migrations_dir(self, app_dir: Path) -> None:
        """
        Creates the migrations directory for an app and generates the __init__.py file.

        Args:
            app_dir: The Path object for the app's directory.
        """
        migrations_dir = app_dir / 'migrations'
        migrations_dir.mkdir(exist_ok=True)

        template_name = f'{self.template_base_dir}/migrations/__init__.py.template'
        self.file_renderer.render_template(
            template_name,
            migrations_dir / '__init__.py'
        )

    def _generate_tests_dir(self, app_dir: Path) -> None:
        """
        Creates the tests directory for an app and generates a basic __init__.py and test_models.py.

        Args:
            app_dir: The Path object for the app's directory.
        """
        tests_dir = app_dir / 'tests'
        tests_dir.mkdir(exist_ok=True)

        template_name_init = f'{self.template_base_dir}/tests/__init__.py.template'
        self.file_renderer.render_template(
            template_name_init,
            tests_dir / '__init__.py'
        )

        template_name_test_models = f'{self.template_base_dir}/tests/test_models.py.template'
        self.file_renderer.render_template(
            template_name_test_models,
            tests_dir / 'test_models.py'
        )
        
    def _determine_app_type(self, app_name: str) -> str:
        """
        Determine the type of app based on name or configuration.
        
        Args:
            app_name: The name of the app.
            
        Returns:
            The app type as a string ('standard', 'api', 'auth', etc.)
        """
        # Check if app type is specified in config
        # app_types = self.config['app_types'] or {}
        # if app_name in app_types:
        #     return app_types[app_name]
            
        # Infer from app name
        if app_name.endswith('_api') or app_name.startswith('api_'):
            return 'api'
        elif app_name in ['users', 'accounts', 'authentication', 'auth']:
            return 'auth'
            
        # Default to standard app
        return 'standard'
    
    def _should_add_feature(self, app_name: str, feature: str) -> bool:
        """
        Determine if a feature should be added to an app.
        
        Args:
            app_name: The name of the app.
            feature: The feature to check.
            
        Returns:
            True if the feature should be added, False otherwise.
        """
        # Check app-specific features in config
        # app_features = self.config['app_features'] or {}
        # if app_name in app_features and feature in app_features[app_name]:
        #     return app_features[app_name][feature]
            
        # Check global features
        # global_features = self.config['global_features'] or {}
        # if feature in global_features:
        #     return global_features[feature]
            
        # Default feature settings
        default_features = {
            'forms': False,
            'signals': False,
            'model_views': False
        }
        
        return default_features.get(feature, False)
