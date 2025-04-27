class DjangoBoilerplateError(Exception):
    """Base exception class for all boilerplate generator exceptions"""
    pass


class InvalidProjectNameError(DjangoBoilerplateError):
    """Raised when an invalid project name is provided"""
    
    def __init__(self, name: str):
        self.name = name
        super().__init__(
            f"'{name}' is not a valid project name. "
            "Project names must:\n"
            "- Start with a letter\n"
            "- Contain only letters, numbers, and underscores\n"
            "- Be a valid Python identifier"
        )


class InvalidAppNameError(DjangoBoilerplateError):
    """Raised when an invalid app name is provided"""
    
    def __init__(self, name: str):
        self.name = name
        super().__init__(
            f"'{name}' is not a valid app name. "
            "App names must:\n"
            "- Start with a lowercase letter\n"
            "- Contain only lowercase letters, numbers, and underscores\n"
            "- Be a valid Python identifier"
        )


class TemplateRenderError(DjangoBoilerplateError):
    """Raised when there's an error during template rendering."""
    # Corrected: Accept the original exception as an argument
    def __init__(self, message: str, error: Exception):
        super().__init__(message)
        self.original_error = error
        self.message = message # Store the message separately if needed

    def __str__(self):
        return f"{self.message} (Original error: {self.original_error})"


class DirectoryCreationError(DjangoBoilerplateError):
    """Raised when unable to create project directories"""
    
    def __init__(self, path: str, error: str):
        self.path = path
        self.error = error
        super().__init__(
            f"Failed to create directory '{path}': {error}"
        )


class FileGenerationError(DjangoBoilerplateError):
    """Raised when unable to generate a file"""
    
    def __init__(self, file_path: str, error: str):
        self.file_path = file_path
        self.error = error
        super().__init__(
            f"Failed to generate file '{file_path}': {error}"
        )


class ConfigurationError(DjangoBoilerplateError):
    """Raised when there's an error in the configuration"""
    
    def __init__(self, setting: str, error: str):
        self.setting = setting
        self.error = error
        super().__init__(
            f"Configuration error in '{setting}': {error}"
        )


class DependencyError(DjangoBoilerplateError):
    """Raised when a required dependency is missing"""
    
    def __init__(self, dependency: str, reason: str):
        self.dependency = dependency
        self.reason = reason
        super().__init__(
            f"Missing required dependency '{dependency}': {reason}"
        )


class EnvironmentError(DjangoBoilerplateError):
    """Raised when there's an environment-specific error"""
    
    def __init__(self, env: str, error: str):
        self.env = env
        self.error = error
        super().__init__(
            f"Environment '{env}' configuration error: {error}"
        )


class InvalidDirectoryNameError(Exception):
    """Base exception class for all boilerplate generator exceptions"""
    pass

class StructureValidationError(Exception):
    """Base exception class for all boilerplate generator exceptions"""
    pass

class InvalidPathError(Exception):
    """Base exception class for all boilerplate generator exceptions"""
    pass
