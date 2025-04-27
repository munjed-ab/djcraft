import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

from generator.app_generator import (
    AppGenerator, AppBuilder, StandardAppStrategy, 
    ApiAppStrategy, AuthAppStrategy, FormDecorator,
    SignalsDecorator, ModelViewsDecorator
)
from core.project_structure_manager import ProjectStructureManager
from generator.file_renderer import FileRenderer
from generator.requirements_manager import RequirementsManager


class TestAppGenerator(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.structure_manager = MagicMock(spec=ProjectStructureManager)
        self.structure_manager.project_path = Path('/fake/path')
        self.structure_manager.project_name = 'test_project'
        self.structure_manager.structure = {
            'apps': {
                'blog': 'apps/blog',
                'api_posts': 'apps/api_posts',
                'users': 'apps/users'
            }
        }
        
        self.file_renderer = MagicMock(spec=FileRenderer)
        self.requirements_manager = MagicMock(spec=RequirementsManager)
        
        # Create config with app types and features
        self.config = {
            'app_types': {
                'blog': 'standard',
                'api_posts': 'api',
                'users': 'auth'
            },
            'app_features': {
                'blog': {
                    'forms': True,
                    'model_views': True
                }
            },
            'global_features': {
                'signals': True
            }
        }
        
        # Create the generator
        self.app_generator = AppGenerator(
            self.structure_manager,
            self.file_renderer,
            self.requirements_manager,
            self.config
        )
    
    def test_determine_app_type(self):
        # Test explicit config
        self.assertEqual(self.app_generator._determine_app_type('blog'), 'standard')
        self.assertEqual(self.app_generator._determine_app_type('api_posts'), 'api')
        self.assertEqual(self.app_generator._determine_app_type('users'), 'auth')
        
        # Test naming convention inference
        self.assertEqual(self.app_generator._determine_app_type('new_api'), 'api')
        self.assertEqual(self.app_generator._determine_app_type('accounts'), 'auth')
        self.assertEqual(self.app_generator._determine_app_type('products'), 'standard')
    
    def test_should_add_feature(self):
        # Test app-specific features
        self.assertTrue(self.app_generator._should_add_feature('blog', 'forms'))
        self.assertTrue(self.app_generator._should_add_feature('blog', 'model_views'))
        
        # Test global features
        self.assertTrue(self.app_generator._should_add_feature('api_posts', 'signals'))
        
        # Test default features
        self.assertFalse(self.app_generator._should_add_feature('api_posts', 'forms'))
    
    @patch('generator.app_generator.AppBuilder')
    def test_generate_standard_app_files(self, mock_builder):
        # Setup mock builder
        mock_builder_instance = MagicMock()
        mock_builder.return_value = mock_builder_instance
        
        # Call the method
        self.app_generator._generate_standard_app_files('blog', Path('/fake/path/apps/blog'), 'apps/blog')
        
        # Verify builder was created with correct parameters
        mock_builder.assert_called_once()
        
        # Verify strategy and features were added
        mock_builder_instance.with_strategy.assert_called_once()
        self.assertEqual(mock_builder_instance.with_feature.call_count, 3)  # forms, signals, model_views
        mock_builder_instance.build.assert_called_once()


class TestAppBuilder(unittest.TestCase):
    def setUp(self):
        self.app_name = 'test_app'
        self.app_dir = Path('/fake/path/apps/test_app')
        self.app_import_path = 'apps.test_app'
        self.file_renderer = MagicMock(spec=FileRenderer)
        self.template_base_dir = 'app_template'
        
        self.builder = AppBuilder(
            self.app_name,
            self.app_dir,
            self.app_import_path,
            self.file_renderer,
            self.template_base_dir
        )
    
    def test_with_strategy(self):
        strategy = MagicMock(spec=StandardAppStrategy)
        result = self.builder.with_strategy(strategy)
        
        self.assertEqual(self.builder.strategy, strategy)
        self.assertEqual(result, self.builder)  # Should return self for chaining
    
    def test_with_feature(self):
        decorator = MagicMock(spec=FormDecorator)
        result = self.builder.with_feature(decorator)
        
        self.assertIn(decorator, self.builder.decorators)
        self.assertEqual(result, self.builder)  # Should return self for chaining
    
    def test_build(self):
        # Setup mocks
        strategy = MagicMock(spec=StandardAppStrategy)
        decorator1 = MagicMock(spec=FormDecorator)
        decorator2 = MagicMock(spec=SignalsDecorator)
        
        # Configure builder
        self.builder.with_strategy(strategy)
        self.builder.with_feature(decorator1)
        self.builder.with_feature(decorator2)
        
        # Build
        self.builder.build()
        
        # Verify strategy was called
        strategy.generate_app_files.assert_called_once_with(
            self.app_name, self.app_dir, self.app_import_path,
            self.file_renderer, self.template_base_dir
        )
        
        # Verify decorators were called
        decorator1.add_feature.assert_called_once_with(self.app_name, self.app_import_path)
        decorator2.add_feature.assert_called_once_with(self.app_name, self.app_import_path)


if __name__ == '__main__':
    unittest.main()