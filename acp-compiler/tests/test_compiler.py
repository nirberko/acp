"""Tests for the main compiler module."""

import tempfile
from pathlib import Path

import pytest

from acp_compiler.compiler import (
    CompilationError,
    compile_spec,
    compile_spec_file,
    validate_spec_file,
)


class TestCompileSpec:
    """Tests for compile_spec function."""

    def test_compile_minimal_spec(self):
        """Test compiling minimal valid spec."""
        yaml_content = """
version: "0.1"
project:
  name: test-project
"""
        ir = compile_spec(yaml_content, check_env=False, resolve_credentials=False)
        assert ir.version == "0.1"
        assert ir.project_name == "test-project"

    def test_compile_full_spec(self, monkeypatch):
        """Test compiling a complete spec."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        yaml_content = """
version: "0.1"
project:
  name: full-test

providers:
  llm:
    openai:
      api_key: env:OPENAI_API_KEY
      default_params:
        temperature: 0.7

policies:
  - name: default
    budgets:
      timeout_seconds: 60

agents:
  - name: assistant
    provider: openai
    model:
      preference: gpt-4
    instructions: You are helpful.
    policy: default

workflows:
  - name: main
    entry: start
    steps:
      - id: start
        type: llm
        agent: assistant
        next: end
      - id: end
        type: end
"""
        ir = compile_spec(yaml_content, check_env=True, resolve_credentials=True)

        assert ir.project_name == "full-test"
        assert "openai" in ir.providers
        assert ir.providers["openai"].api_key.value == "sk-test"
        assert "default" in ir.policies
        assert "assistant" in ir.agents
        assert "main" in ir.workflows

    def test_compile_invalid_yaml(self):
        """Test that invalid YAML raises CompilationError."""
        yaml_content = """
version: "0.1"
project:
  name: test
    invalid: indent
"""
        with pytest.raises(CompilationError) as exc_info:
            compile_spec(yaml_content, check_env=False)
        assert "Parse error" in str(exc_info.value)

    def test_compile_validation_failure(self):
        """Test that validation errors raise CompilationError."""
        yaml_content = """
version: "0.1"
project:
  name: test

agents:
  - name: assistant
    provider: nonexistent  # Invalid provider
    model:
      preference: gpt-4
    instructions: Help.
"""
        with pytest.raises(CompilationError) as exc_info:
            compile_spec(yaml_content, check_env=False)
        assert "Validation failed" in str(exc_info.value)
        assert exc_info.value.validation_result is not None
        assert not exc_info.value.validation_result.is_valid

    def test_compile_with_all_step_types(self, monkeypatch):
        """Test compiling spec with all step types."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        yaml_content = """
version: "0.1"
project:
  name: all-steps

providers:
  llm:
    openai:
      api_key: env:OPENAI_API_KEY

servers:
  - name: fs
    command: ["node", "fs-server"]

capabilities:
  - name: read_file
    server: fs
    method: readFile

agents:
  - name: assistant
    provider: openai
    model:
      preference: gpt-4
    instructions: Help.
    allow:
      - read_file

workflows:
  - name: complex
    entry: start
    steps:
      - id: start
        type: llm
        agent: assistant
        save_as: result
        next: check
      - id: check
        type: condition
        condition: "$state.result == 'continue'"
        on_true: read
        on_false: approve
      - id: read
        type: call
        capability: read_file
        args:
          path: /tmp/test.txt
        next: end
      - id: approve
        type: human_approval
        payload: $state.result
        on_approve: end
        on_reject: end
      - id: end
        type: end
"""
        ir = compile_spec(yaml_content, check_env=False, resolve_credentials=False)

        workflow = ir.workflows["complex"]
        assert len(workflow.steps) == 5
        assert workflow.steps["start"].type.value == "llm"
        assert workflow.steps["check"].type.value == "condition"
        assert workflow.steps["read"].type.value == "call"
        assert workflow.steps["approve"].type.value == "human_approval"
        assert workflow.steps["end"].type.value == "end"


class TestCompileSpecFile:
    """Tests for compile_spec_file function."""

    def test_compile_existing_file(self, monkeypatch):
        """Test compiling an existing YAML file."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        yaml_content = """
version: "0.1"
project:
  name: file-test

providers:
  llm:
    openai:
      api_key: env:OPENAI_API_KEY

agents:
  - name: assistant
    provider: openai
    model:
      preference: gpt-4
    instructions: Help.

workflows:
  - name: main
    entry: start
    steps:
      - id: start
        type: llm
        agent: assistant
        next: end
      - id: end
        type: end
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            ir = compile_spec_file(f.name, check_env=False, resolve_credentials=False)
            assert ir.project_name == "file-test"

            # Cleanup
            Path(f.name).unlink()

    def test_compile_nonexistent_file(self):
        """Test that non-existent file raises CompilationError."""
        with pytest.raises(CompilationError) as exc_info:
            compile_spec_file("/nonexistent/path.yaml")
        assert "Parse error" in str(exc_info.value)

    def test_compile_file_with_path_object(self, monkeypatch):
        """Test compiling file using Path object."""
        yaml_content = """
version: "0.1"
project:
  name: path-test
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            ir = compile_spec_file(Path(f.name), check_env=False)
            assert ir.project_name == "path-test"

            Path(f.name).unlink()


class TestValidateSpecFile:
    """Tests for validate_spec_file function."""

    def test_validate_valid_file(self):
        """Test validating a valid YAML file."""
        yaml_content = """
version: "0.1"
project:
  name: valid-test
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            result = validate_spec_file(f.name, check_env=False)
            assert result.is_valid is True

            Path(f.name).unlink()

    def test_validate_invalid_file(self):
        """Test validating a file with validation errors."""
        yaml_content = """
version: "0.1"
project:
  name: invalid-test

agents:
  - name: assistant
    provider: nonexistent
    model:
      preference: gpt-4
    instructions: Help.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()

            result = validate_spec_file(f.name, check_env=False)
            assert result.is_valid is False
            assert len(result.errors) > 0

            Path(f.name).unlink()

    def test_validate_nonexistent_file(self):
        """Test that non-existent file raises CompilationError."""
        with pytest.raises(CompilationError) as exc_info:
            validate_spec_file("/nonexistent/path.yaml")
        assert "Parse error" in str(exc_info.value)
