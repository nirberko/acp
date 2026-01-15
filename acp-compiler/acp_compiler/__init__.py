"""ACP Compiler - YAML compilation and validation for ACP."""

from acp_compiler.compiler import (
    CompilationError,
    compile_spec,
    compile_spec_file,
    validate_spec_file,
)
from acp_compiler.credentials import (
    CredentialError,
    get_env_var_name,
    is_env_reference,
    resolve_env_var,
)
from acp_compiler.ir_generator import IRGenerationError, generate_ir
from acp_compiler.parser import ParseError, parse_yaml, parse_yaml_file
from acp_compiler.validator import ValidationError, ValidationResult, validate_spec

__all__ = [
    "CompilationError",
    "CredentialError",
    "IRGenerationError",
    "ParseError",
    "ValidationError",
    "ValidationResult",
    "compile_spec",
    "compile_spec_file",
    "generate_ir",
    "get_env_var_name",
    "is_env_reference",
    "parse_yaml",
    "parse_yaml_file",
    "resolve_env_var",
    "validate_spec",
    "validate_spec_file",
]
