"""Tests for schema block functionality."""

from agentform_compiler.agentform_ast import SchemaBlock
from agentform_compiler.agentform_normalizer import normalize_agentform
from agentform_compiler.agentform_parser import parse_agentform
from agentform_compiler.agentform_resolver import resolve_references
from agentform_compiler.agentform_validator import validate_agentform
from agentform_compiler.ir_generator import generate_ir
from agentform_schema.ir import ResolvedSchema


class TestSchemaBlockParsing:
    """Test parsing of schema blocks."""

    def test_parse_simple_schema(self) -> None:
        """Test parsing a simple schema block with scalar types."""
        content = """
        agentform { version = "0.1" project = "test" }

        schema "person" {
            name = string
            age = number
            active = boolean
        }
        """
        result = parse_agentform(content)

        assert len(result.schemas) == 1
        schema = result.schemas[0]
        assert isinstance(schema, SchemaBlock)
        assert schema.name == "person"

        fields = schema.get_fields()
        assert fields["name"] == "string"
        assert fields["age"] == "number"
        assert fields["active"] == "boolean"

    def test_parse_schema_with_list_types(self) -> None:
        """Test parsing a schema with list types."""
        content = """
        agentform { version = "0.1" project = "test" }

        schema "data" {
            tags = list(string)
            scores = list(number)
            flags = list(boolean)
        }
        """
        result = parse_agentform(content)

        assert len(result.schemas) == 1
        schema = result.schemas[0]

        fields = schema.get_fields()
        assert fields["tags"] == "list(string)"
        assert fields["scores"] == "list(number)"
        assert fields["flags"] == "list(boolean)"

    def test_parse_multiple_schemas(self) -> None:
        """Test parsing multiple schema blocks."""
        content = """
        agentform { version = "0.1" project = "test" }

        schema "person" {
            name = string
        }

        schema "address" {
            city = string
            zip = number
        }
        """
        result = parse_agentform(content)

        assert len(result.schemas) == 2
        assert result.schemas[0].name == "person"
        assert result.schemas[1].name == "address"

    def test_get_schema_by_name(self) -> None:
        """Test retrieving schema by name from AgentformFile."""
        content = """
        agentform { version = "0.1" project = "test" }

        schema "person" {
            name = string
        }

        schema "address" {
            city = string
        }
        """
        result = parse_agentform(content)

        person = result.get_schema("person")
        assert person is not None
        assert person.name == "person"

        address = result.get_schema("address")
        assert address is not None
        assert address.name == "address"

        # Non-existent schema returns None
        assert result.get_schema("missing") is None


class TestSchemaSymbolResolution:
    """Test schema symbol table and reference resolution."""

    def test_schema_symbols_registered(self) -> None:
        """Test that schema symbols are registered in symbol table."""
        content = """
        agentform { version = "0.1" project = "test" }

        schema "person" {
            name = string
        }

        schema "address" {
            city = string
        }
        """
        agentform_file = parse_agentform(content)
        result = resolve_references(agentform_file)

        assert "schema.person" in result.symbols
        assert "schema.address" in result.symbols
        assert result.symbols["schema.person"].kind == "schema"
        assert result.symbols["schema.address"].kind == "schema"

    def test_duplicate_schema_error(self) -> None:
        """Test that duplicate schema names produce an error."""
        content = """
        agentform { version = "0.1" project = "test" }

        schema "person" {
            name = string
        }

        schema "person" {
            age = number
        }
        """
        agentform_file = parse_agentform(content)
        result = resolve_references(agentform_file)

        assert not result.is_valid
        assert any("Duplicate schema" in str(e) for e in result.errors)

    def test_agent_output_schema_resolved(self) -> None:
        """Test that agent output_schema references are resolved."""
        content = """
        agentform { version = "0.1" project = "test" }

        schema "response" {
            answer = string
        }

        model "gpt4" {
            provider = provider.llm.openai.default
            id = "gpt-4o"
        }

        agent "assistant" {
            model = model.gpt4
            instructions = "Be helpful."
            output_schema = schema.response
        }
        """
        agentform_file = parse_agentform(content)
        result = resolve_references(agentform_file)

        # Schema reference should be resolved (only unresolved provider issue)
        schema_errors = [e for e in result.errors if "schema" in str(e).lower()]
        assert len(schema_errors) == 0

    def test_unresolved_output_schema_error(self) -> None:
        """Test that unresolved output_schema produces an error."""
        content = """
        agentform { version = "0.1" project = "test" }

        model "gpt4" {
            provider = provider.llm.openai.default
            id = "gpt-4o"
        }

        agent "assistant" {
            model = model.gpt4
            instructions = "Be helpful."
            output_schema = schema.nonexistent
        }
        """
        agentform_file = parse_agentform(content)
        result = resolve_references(agentform_file)

        assert not result.is_valid
        assert any("Unresolved reference: schema.nonexistent" in str(e) for e in result.errors)


class TestSchemaValidation:
    """Test schema validation rules."""

    def test_valid_scalar_types(self) -> None:
        """Test that valid scalar types pass validation."""
        content = """
        agentform { version = "0.1" project = "test" }

        schema "data" {
            text = string
            count = number
            flag = boolean
        }
        """
        agentform_file = parse_agentform(content)
        resolution = resolve_references(agentform_file)
        result = validate_agentform(agentform_file, resolution)

        # No schema-related errors
        schema_errors = [e for e in result.errors if "schema" in e.path]
        assert len(schema_errors) == 0

    def test_valid_list_types(self) -> None:
        """Test that valid list types pass validation."""
        content = """
        agentform { version = "0.1" project = "test" }

        schema "data" {
            names = list(string)
            scores = list(number)
            flags = list(boolean)
        }
        """
        agentform_file = parse_agentform(content)
        resolution = resolve_references(agentform_file)
        result = validate_agentform(agentform_file, resolution)

        # No schema-related errors
        schema_errors = [e for e in result.errors if "schema" in e.path]
        assert len(schema_errors) == 0

    def test_invalid_type_error(self) -> None:
        """Test that invalid types produce an error."""
        content = """
        agentform { version = "0.1" project = "test" }

        schema "data" {
            field = invalid_type
        }
        """
        agentform_file = parse_agentform(content)
        resolution = resolve_references(agentform_file)
        result = validate_agentform(agentform_file, resolution)

        assert not result.is_valid
        assert any("Invalid field type" in e.message for e in result.errors)

    def test_invalid_list_item_type_error(self) -> None:
        """Test that invalid list item types produce an error."""
        content = """
        agentform { version = "0.1" project = "test" }

        schema "data" {
            items = list(invalid)
        }
        """
        agentform_file = parse_agentform(content)
        resolution = resolve_references(agentform_file)
        result = validate_agentform(agentform_file, resolution)

        assert not result.is_valid
        assert any("Invalid list item type" in e.message for e in result.errors)

    def test_empty_schema_error(self) -> None:
        """Test that empty schemas produce an error."""
        content = """
        agentform { version = "0.1" project = "test" }

        schema "empty" {
        }
        """
        agentform_file = parse_agentform(content)
        resolution = resolve_references(agentform_file)
        result = validate_agentform(agentform_file, resolution)

        assert not result.is_valid
        assert any("at least one field" in e.message for e in result.errors)

    def test_output_schema_must_be_reference(self) -> None:
        """Test that output_schema must be a schema reference."""
        content = """
        agentform { version = "0.1" project = "test" }

        model "gpt4" {
            provider = provider.llm.openai.default
            id = "gpt-4o"
        }

        agent "assistant" {
            model = model.gpt4
            instructions = "Be helpful."
            output_schema = "not_a_reference"
        }
        """
        agentform_file = parse_agentform(content)
        resolution = resolve_references(agentform_file)
        result = validate_agentform(agentform_file, resolution)

        assert not result.is_valid
        assert any("must be a schema reference" in e.message for e in result.errors)


class TestSchemaIRGeneration:
    """Test schema IR generation."""

    def test_generate_schema_ir(self) -> None:
        """Test generating schema IR from AST."""
        content = """
        agentform { version = "0.1" project = "test" }

        variable "openai_api_key" { default = "env:OPENAI_API_KEY" }

        provider "llm.openai" "default" {
            api_key = var.openai_api_key
        }

        model "gpt4" {
            provider = provider.llm.openai.default
            id = "gpt-4o"
        }

        schema "person" {
            name = string
            age = number
            active = boolean
            hobbies = list(string)
        }

        agent "assistant" {
            model = model.gpt4
            instructions = "Be helpful."
        }

        workflow "test" {
            entry = step.start
            step "start" {
                type = "end"
            }
        }
        """
        agentform_file = parse_agentform(content)
        resolution = resolve_references(agentform_file)
        spec = normalize_agentform(agentform_file, resolution)
        ir = generate_ir(spec, resolve_credentials=False, agentform_file=agentform_file)

        assert "person" in ir.schemas
        schema = ir.schemas["person"]
        assert isinstance(schema, ResolvedSchema)
        assert schema.name == "person"

        # Check fields
        assert "name" in schema.fields
        assert schema.fields["name"].type == "string"

        assert "age" in schema.fields
        assert schema.fields["age"].type == "number"

        assert "active" in schema.fields
        assert schema.fields["active"].type == "boolean"

        assert "hobbies" in schema.fields
        assert schema.fields["hobbies"].type == "list"
        assert schema.fields["hobbies"].item_type == "string"

    def test_agent_output_schema_name_in_ir(self) -> None:
        """Test that agent output_schema_name is set in IR."""
        content = """
        agentform { version = "0.1" project = "test" }

        variable "openai_api_key" { default = "env:OPENAI_API_KEY" }

        provider "llm.openai" "default" {
            api_key = var.openai_api_key
        }

        model "gpt4" {
            provider = provider.llm.openai.default
            id = "gpt-4o"
        }

        schema "response" {
            answer = string
            confidence = number
        }

        agent "assistant" {
            model = model.gpt4
            instructions = "Be helpful."
            output_schema = schema.response
        }

        workflow "test" {
            entry = step.start
            step "start" {
                type = "end"
            }
        }
        """
        agentform_file = parse_agentform(content)
        resolution = resolve_references(agentform_file)
        spec = normalize_agentform(agentform_file, resolution)
        ir = generate_ir(spec, resolve_credentials=False, agentform_file=agentform_file)

        assert "assistant" in ir.agents
        agent = ir.agents["assistant"]
        assert agent.output_schema_name == "response"

    def test_agent_without_output_schema(self) -> None:
        """Test that agents without output_schema have None."""
        content = """
        agentform { version = "0.1" project = "test" }

        variable "openai_api_key" { default = "env:OPENAI_API_KEY" }

        provider "llm.openai" "default" {
            api_key = var.openai_api_key
        }

        model "gpt4" {
            provider = provider.llm.openai.default
            id = "gpt-4o"
        }

        agent "assistant" {
            model = model.gpt4
            instructions = "Be helpful."
        }

        workflow "test" {
            entry = step.start
            step "start" {
                type = "end"
            }
        }
        """
        agentform_file = parse_agentform(content)
        resolution = resolve_references(agentform_file)
        spec = normalize_agentform(agentform_file, resolution)
        ir = generate_ir(spec, resolve_credentials=False, agentform_file=agentform_file)

        assert "assistant" in ir.agents
        agent = ir.agents["assistant"]
        assert agent.output_schema_name is None


class TestSchemaIntegration:
    """Integration tests for full schema workflow."""

    def test_full_schema_workflow(self) -> None:
        """Test complete schema workflow from parsing to IR."""
        content = """
        agentform { version = "0.1" project = "test" }

        variable "openai_api_key" { default = "env:OPENAI_API_KEY" }

        provider "llm.openai" "default" {
            api_key = var.openai_api_key
        }

        model "gpt4o_mini" {
            provider = provider.llm.openai.default
            id = "gpt-4o-mini"
        }

        model "gpt4o" {
            provider = provider.llm.openai.default
            id = "gpt-4o"
        }

        schema "person" {
            name = string
            age = number
            hobbies = list(string)
        }

        agent "assistant" {
            model = model.gpt4o_mini
            fallback_models = [model.gpt4o]
            instructions = "Extract person information."
            output_schema = schema.person
        }

        workflow "extract" {
            entry = step.start
            step "start" {
                type = "end"
            }
        }
        """
        # Parse
        agentform_file = parse_agentform(content)
        assert len(agentform_file.schemas) == 1
        assert agentform_file.schemas[0].name == "person"

        # Resolve
        resolution = resolve_references(agentform_file)
        assert "schema.person" in resolution.symbols
        assert resolution.is_valid

        # Validate
        validation = validate_agentform(agentform_file, resolution)
        assert validation.is_valid

        # Normalize and generate IR
        spec = normalize_agentform(agentform_file, resolution)
        ir = generate_ir(spec, resolve_credentials=False, agentform_file=agentform_file)

        # Verify schema in IR
        assert "person" in ir.schemas
        schema = ir.schemas["person"]
        assert schema.fields["name"].type == "string"
        assert schema.fields["age"].type == "number"
        assert schema.fields["hobbies"].type == "list"
        assert schema.fields["hobbies"].item_type == "string"

        # Verify agent references schema
        assert ir.agents["assistant"].output_schema_name == "person"
