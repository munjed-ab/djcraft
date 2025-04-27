from typing import Any, Dict

from core.configuration_manager import ConfigurationManager
from core.project_structure_manager import ProjectStructureManager

from ..file_renderer import FileRenderer
from ..requirements_manager import RequirementsManager
from .base import BaseServiceGenerator


class RedisGenerator(BaseServiceGenerator):
    """
    Generates configuration and updates settings for integrating Redis.
    Redis is often used as a cache or Celery broker.
    """
    service_name = "redis"
    def __init__(self, structure_manager: ProjectStructureManager, file_renderer: FileRenderer, requirements_manager: RequirementsManager, options: Dict[str, Any]):
        """
        Initialize the RedisGenerator.

        Args:
            structure_manager: The ProjectStructureManager instance.
            file_renderer: The FileRenderer instance.
            requirements_manager: The RequirementsManager instance.
            options: Service-specific options for Redis.
        """
        self.structure_manager = structure_manager
        self.file_renderer = file_renderer
        self.requirements_manager = requirements_manager
        self.project_path = structure_manager.project_path
        self.options = options or {}

        # Redis typically doesn't require dedicated template files,
        # but rather updates to settings.py and requirements.txt.
        # If you have a specific Redis config file template, define its base dir here.
        # self.template_base_dir = 'redis_template'


    def generate(self) -> None:
        """
        Generates Redis-related configurations and updates.
        """
        # Update settings files with Redis configuration
        self._update_settings_files()

        # Add required packages to requirements.txt
        self._add_required_packages()

        # Note: Docker configuration for Redis is handled by DockerGenerator
        # based on the presence of the 'redis' service.


    def _update_settings_files(self) -> None:
        """
        Updates the settings files (specifically base.py) with Redis configuration.
        Adds cache settings to point to Redis.
        """
        core_path = self.structure_manager.get_core_path()
        settings_path = core_path / 'settings' / 'base.py'

        if not settings_path.exists():
            print(f"Warning: base.py not found at {settings_path}. Cannot add Redis settings.")
            return
        
        redis_defaults = ConfigurationManager.get_service_default_options('redis')

        # Get Redis host and port options with defaults
        redis_host = self.options.get('host', redis_defaults.get('host', 'redis')) # 'redis' is common hostname in Docker
        redis_port = self.options.get('port', redis_defaults.get('port', 6379))

        redis_settings = f"""

# Redis Configuration (as Cache)
# Used for caching, sessions, and potentially as a Celery broker
CACHES = {{
    'default': {{
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://{redis_host}:{redis_port}/1', # Use DB 1 for cache
        'OPTIONS': {{
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }}
    }}
}}

# Optional: Configure Redis for sessions if needed
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# SESSION_CACHE_ALIAS = 'default'

# Optional: Configure Redis as Celery Broker (if Celery is also included)
# This setting is also handled by CeleryGenerator, ensure consistency or prioritize one
# CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://{redis_host}:{redis_port}/0') # Use DB 0 for Celery broker
# CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://{redis_host}:{redis_port}/0')

"""
        # Need to add 'os' import if not already present in base.py template
        # This is handled in CeleryGenerator's settings update, but good to be aware.

        # Read existing content
        existing_content = ""
        with open(settings_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        # Only append if Redis cache settings are not already present
        if "'BACKEND': 'django_redis.cache.RedisCache'" not in existing_content:
             # Add os import if not present (might be added by CeleryGenerator already)
            if 'import os' not in existing_content:
                 existing_content = 'import os\n' + existing_content
                 if not existing_content.startswith('\n'):
                     existing_content = '\n' + existing_content

            with open(settings_path, 'w', encoding='utf-8') as f:
                f.write(existing_content + redis_settings)


    def _add_required_packages(self) -> None:
        """
        Adds required Python packages for Redis integration to requirements.txt.
        """
        required_packages = [
            'django-redis>=5.0.0', # Package for Django Redis cache backend
            # 'redis>=4.0.0', # The underlying redis-py library, often needed
        ]
        # The 'redis' package is added by CeleryGenerator if Redis is the broker,
        # but it's good practice to add it here too if Redis is used for other purposes (like caching).
        # We can add it unconditionally or check if it's already added.
        # Using the RequirementsManager's set handles uniqueness automatically.
        required_packages.append('redis>=4.0.0')


        self.requirements_manager.add_packages(required_packages)

