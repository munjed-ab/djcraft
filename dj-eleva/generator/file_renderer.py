from pathlib import Path
from typing import Any, Dict, Optional

from .rendering import Jinja2RendererStrategy, RendererStrategy


class FileRenderer:
    """
    Handles rendering templates to generate project files using the Strategy pattern.
    """
    def __init__(self, template_dir: str, renderer_strategy: Optional[RendererStrategy] = None):
        """
        Initialize the FileRenderer with the template directory and renderer strategy.

        Args:
            template_dir: The path to the directory containing template files.
            renderer_strategy: The strategy to use for rendering templates. Defaults to Jinja2RendererStrategy.
        """
        self.template_dir = template_dir
        self.renderer = renderer_strategy or Jinja2RendererStrategy(template_dir)


    def render_template(self, template_name: str, output_path: Path, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Render a template with the given context and write the output to a file.

        Args:
            template_name: The name of the template file within the template directory.
                           Can include subdirectories (e.g., 'project_template/core/settings/base.py.template').
            output_path: The full filesystem path where the rendered content should be written.
            context: A dictionary containing data to be passed to the template.
        """
        self.renderer.render_template(template_name, output_path, context)
        
    def render_template_to_string(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Render a template with the given context and return the result as a string.
        
        Args:
            template_name: The name of the template file within the template directory.
            context: A dictionary containing data to be passed to the template.
            
        Returns:
            The rendered template as a string.
        """
        return self.renderer.render_template_to_string(template_name, context)

