"""Utility module for managing LangChain provider packages."""

import importlib
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

    from agentform_compiler.agentform_ast import AgentformFile
    from agentform_schema.ir import CompiledSpec


class MissingProviderPackagesError(Exception):
    """Raised when required provider packages are missing."""

    def __init__(self, missing_packages: list[tuple[str, str]]):
        """Initialize error with missing packages.

        Args:
            missing_packages: List of (provider_type, package_name) tuples
        """
        self.missing_packages = missing_packages
        super().__init__(f"Missing {len(missing_packages)} provider package(s)")


def detect_required_providers(agentform_file: "AgentformFile") -> set[str]:
    """Extract provider types from parsed Agentform file.

    Args:
        agentform_file: Parsed Agentform file

    Returns:
        Set of provider types (e.g., {"openai", "anthropic"})
    """
    providers = set()
    for provider in agentform_file.providers:
        # Extract vendor from "llm.{vendor}" format
        parts = provider.provider_type.split(".")
        if len(parts) >= 2 and parts[0] == "llm":
            vendor = ".".join(parts[1:])  # Handle nested vendor names like "google.vertexai"
            providers.add(vendor)
    return providers


def get_langchain_package(provider_type: str) -> str:
    """Map provider type to LangChain package name.

    Args:
        provider_type: Provider type (e.g., "openai", "anthropic", "google")

    Returns:
        LangChain package name (e.g., "langchain-openai", "langchain-anthropic")
    """
    # Handle special cases where package name doesn't follow simple pattern
    mapping = {
        "google": "langchain-google-genai",
        "google_genai": "langchain-google-genai",
        "google_vertexai": "langchain-google-vertexai",
        "azure": "langchain-azure-openai",
        "azure_openai": "langchain-azure-openai",
        "bedrock": "langchain-aws",
        "bedrock_converse": "langchain-aws",
        "cohere": "langchain-cohere",
        "fireworks": "langchain-fireworks",
        "together": "langchain-together",
        "mistralai": "langchain-mistralai",
        "huggingface": "langchain-huggingface",
        "groq": "langchain-groq",
        "grok": "langchain-xai",
        "xai": "langchain-xai",
        "ollama": "langchain-ollama",
    }

    # Check mapping first
    if provider_type in mapping:
        return mapping[provider_type]

    # Default pattern: langchain-{provider_type}
    # Replace underscores with hyphens for package name
    package_name = provider_type.replace("_", "-")
    return f"langchain-{package_name}"


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed by attempting to import it.

    Args:
        package_name: Package name (e.g., "langchain-openai")

    Returns:
        True if package is installed, False otherwise
    """
    # Convert package name to module name (langchain-openai -> langchain_openai)
    module_name = package_name.replace("-", "_")

    # Try to import the main module
    # For most langchain packages, the main module is the package name
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        # Try alternative import paths for some packages
        # Some packages might have different module structures
        try:
            # Try importing from langchain_integrations
            importlib.import_module(f"langchain_integrations.{module_name}")
            return True
        except ImportError:
            return False


def install_package(package_name: str) -> bool:
    """Install a package using pip.

    Args:
        package_name: Package name to install (e.g., "langchain-openai")

    Returns:
        True if installation succeeded, False otherwise
    """
    try:
        result = subprocess.run(
            ["pip", "install", package_name],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


def validate_provider_packages(compiled: "CompiledSpec", console: "Console | None" = None) -> None:
    """Validate that all required LangChain provider packages are installed.

    Args:
        compiled: Compiled specification with providers
        console: Optional console for output (if None, only raises exception)

    Raises:
        MissingProviderPackagesError: If any required packages are missing
    """
    missing_packages = []

    for _provider_name, provider in compiled.providers.items():
        package_name = get_langchain_package(provider.provider_type)
        if not is_package_installed(package_name):
            missing_packages.append((provider.provider_type, package_name))

    if missing_packages:
        if console:
            console.print("[red]✗ Missing required LangChain provider packages:[/red]")
            for provider_type, package_name in missing_packages:
                console.print(f"  • {provider_type}: {package_name}")
            console.print(
                "\n[yellow]Run 'agentform init' to install missing packages automatically[/yellow]"
            )
            console.print("Or install manually:")
            for _, package_name in missing_packages:
                console.print(f"  pip install {package_name}")
        raise MissingProviderPackagesError(missing_packages)
