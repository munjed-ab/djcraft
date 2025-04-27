# generator/rendering/renderer_strategy.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional


class RendererStrategy(ABC):
    """Abstract base class for renderer strategies implementing the Strategy pattern."""

    @abstractmethod
    def render_template(self, template_name: str, output_path: Path, context: Optional[Dict[str, Any]] = None) -> None:
        """Render a template with the given context and write the output to a file."""
        pass

    @abstractmethod
    def render_template_to_string(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Render a template with the given context and return the result as a string."""
        pass


class Jinja2RendererStrategy(RendererStrategy):
    """Concrete implementation of RendererStrategy using Jinja2."""

    def __init__(self, template_dir: str):
        """Initialize the Jinja2RendererStrategy with the template directory."""
        from jinja2 import Environment, FileSystemLoader, TemplateNotFound
        self.template_dir = template_dir
        self.template_env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
        self.TemplateNotFound = TemplateNotFound

    def render_template(self, template_name: str, output_path: Path, context: Optional[Dict[str, Any]] = None) -> None:
        """Render a template with the given context and write the output to a file."""
        from core.exceptions import TemplateRenderError
        context = context or {}
        original_template_name = template_name

        try:
            template = self.template_env.get_template(template_name)
            rendered_content = template.render(**context)

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the rendered content to the output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)

        except self.TemplateNotFound as e:
            raise TemplateRenderError(f"Template file not found: '{original_template_name}'", e) from e
        except Exception as e:
            raise TemplateRenderError(f"Error rendering template '{original_template_name}' to '{output_path}': {e}", e) from e

    def render_template_to_string(self, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Render a template with the given context and return the result as a string."""
        from core.exceptions import TemplateRenderError
        context = context or {}
        original_template_name = template_name

        try:
            template = self.template_env.get_template(template_name)
            return template.render(**context)
        except self.TemplateNotFound as e:
            raise TemplateRenderError(f"Template file not found: '{original_template_name}'", e) from e
        except Exception as e:
            raise TemplateRenderError(f"Error rendering template '{original_template_name}' to string: {e}", e) from e