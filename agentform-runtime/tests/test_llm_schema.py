"""Tests for LLM executor schema-to-Pydantic conversion."""

from pydantic import BaseModel

from agentform_runtime.llm import LLMExecutor
from agentform_schema.ir import ResolvedSchema, SchemaField


class TestSchemaToPydantic:
    """Test conversion of ResolvedSchema to Pydantic models."""

    def test_convert_scalar_fields(self) -> None:
        """Test converting scalar field types to Pydantic model."""
        schema = ResolvedSchema(
            name="person",
            fields={
                "name": SchemaField(type="string"),
                "age": SchemaField(type="number"),
                "active": SchemaField(type="boolean"),
            },
        )

        executor = LLMExecutor(providers={}, schemas={"person": schema})
        pydantic_model = executor._schema_to_pydantic(schema)

        assert issubclass(pydantic_model, BaseModel)
        assert "name" in pydantic_model.model_fields
        assert "age" in pydantic_model.model_fields
        assert "active" in pydantic_model.model_fields

        # Verify types
        name_field = pydantic_model.model_fields["name"]
        assert name_field.annotation is str

        age_field = pydantic_model.model_fields["age"]
        assert age_field.annotation is float

        active_field = pydantic_model.model_fields["active"]
        assert active_field.annotation is bool

    def test_convert_list_fields(self) -> None:
        """Test converting list field types to Pydantic model."""
        schema = ResolvedSchema(
            name="data",
            fields={
                "tags": SchemaField(type="list", item_type="string"),
                "scores": SchemaField(type="list", item_type="number"),
            },
        )

        executor = LLMExecutor(providers={}, schemas={"data": schema})
        pydantic_model = executor._schema_to_pydantic(schema)

        assert issubclass(pydantic_model, BaseModel)
        assert "tags" in pydantic_model.model_fields
        assert "scores" in pydantic_model.model_fields

        # Verify list types - the annotation is list[str] and list[float]
        tags_field = pydantic_model.model_fields["tags"]
        assert tags_field.annotation is not None
        assert hasattr(tags_field.annotation, "__origin__")  # It's a generic type
        assert tags_field.annotation.__origin__ is list

        scores_field = pydantic_model.model_fields["scores"]
        assert scores_field.annotation is not None
        assert hasattr(scores_field.annotation, "__origin__")
        assert scores_field.annotation.__origin__ is list

    def test_model_is_cached(self) -> None:
        """Test that generated Pydantic models are cached."""
        schema = ResolvedSchema(
            name="test",
            fields={"field": SchemaField(type="string")},
        )

        executor = LLMExecutor(providers={}, schemas={"test": schema})

        model1 = executor._schema_to_pydantic(schema)
        model2 = executor._schema_to_pydantic(schema)

        assert model1 is model2  # Same object due to caching

    def test_model_name_formatting(self) -> None:
        """Test that model names are properly formatted."""
        schema = ResolvedSchema(
            name="user_profile",
            fields={"name": SchemaField(type="string")},
        )

        executor = LLMExecutor(providers={}, schemas={"user_profile": schema})
        pydantic_model = executor._schema_to_pydantic(schema)

        # Name should be title-cased (underscores removed via title())
        assert pydantic_model.__name__ == "UserProfile"

    def test_model_instantiation(self) -> None:
        """Test that generated model can be instantiated with data."""
        schema = ResolvedSchema(
            name="person",
            fields={
                "name": SchemaField(type="string"),
                "age": SchemaField(type="number"),
                "hobbies": SchemaField(type="list", item_type="string"),
            },
        )

        executor = LLMExecutor(providers={}, schemas={"person": schema})
        pydantic_model = executor._schema_to_pydantic(schema)

        # Create instance
        instance = pydantic_model(
            name="Alice",
            age=30.0,
            hobbies=["reading", "coding"],
        )

        # Type checker doesn't know about dynamically created fields
        assert instance.name == "Alice"  # type: ignore[attr-defined]
        assert instance.age == 30.0  # type: ignore[attr-defined]
        assert instance.hobbies == ["reading", "coding"]  # type: ignore[attr-defined]

    def test_model_dump(self) -> None:
        """Test that generated model can be dumped to dict."""
        schema = ResolvedSchema(
            name="response",
            fields={
                "answer": SchemaField(type="string"),
                "confidence": SchemaField(type="number"),
            },
        )

        executor = LLMExecutor(providers={}, schemas={"response": schema})
        pydantic_model = executor._schema_to_pydantic(schema)

        instance = pydantic_model(answer="Yes", confidence=0.95)
        data = instance.model_dump()

        assert data == {"answer": "Yes", "confidence": 0.95}


class TestLLMExecutorWithSchemas:
    """Test LLMExecutor initialization with schemas."""

    def test_init_without_schemas(self) -> None:
        """Test LLMExecutor can be initialized without schemas."""
        executor = LLMExecutor(providers={})
        assert executor._schemas == {}

    def test_init_with_schemas(self) -> None:
        """Test LLMExecutor stores schemas correctly."""
        schema = ResolvedSchema(
            name="test",
            fields={"field": SchemaField(type="string")},
        )

        executor = LLMExecutor(providers={}, schemas={"test": schema})
        assert "test" in executor._schemas
        assert executor._schemas["test"] == schema
