"""LLM integration via LangChain."""

from typing import Any, cast

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, create_model

from agentform_runtime.logging_config import get_logger
from agentform_schema.ir import ResolvedAgent, ResolvedProvider, ResolvedSchema


class LLMError(Exception):
    """Error during LLM execution."""

    pass


# Type mapping from schema types to Python types
_SCHEMA_TYPE_MAP: dict[str, type] = {
    "string": str,
    "number": float,
    "boolean": bool,
}


class LLMExecutor:
    """Executes LLM calls using LangChain."""

    def __init__(
        self,
        providers: dict[str, ResolvedProvider],
        schemas: dict[str, ResolvedSchema] | None = None,
        verbose: bool = False,
    ):
        """Initialize LLM executor.

        Args:
            providers: Resolved provider configurations
            schemas: Resolved schema definitions for structured output
            verbose: Enable verbose logging
        """
        self._providers = providers
        self._schemas = schemas or {}
        self._llm_cache: dict[str, Any] = {}
        self._pydantic_model_cache: dict[str, type[BaseModel]] = {}
        self._verbose = verbose
        self._logger = get_logger("agentform_runtime.llm")

    def _get_llm(self, provider_name: str, model: str, params: dict[str, Any]) -> Any:
        """Get or create an LLM instance.

        Args:
            provider_name: Provider identifier
            model: Model name
            params: Model parameters

        Returns:
            LangChain LLM instance

        Raises:
            LLMError: If provider not found or not supported
        """
        cache_key = f"{provider_name}:{model}"
        if cache_key in self._llm_cache:
            self._logger.debug("llm_cache_hit", provider=provider_name, model=model)
            return self._llm_cache[cache_key]

        self._logger.debug("llm_creation_start", provider=provider_name, model=model, params=params)

        provider = self._providers.get(provider_name)
        if not provider:
            raise LLMError(f"Provider '{provider_name}' not found")

        api_key = provider.api_key.value
        if not api_key:
            raise LLMError(f"API key for provider '{provider_name}' not resolved")

        # Build params for init_chat_model
        llm_params: dict[str, Any] = {
            "model": model,
            "model_provider": provider.provider_type,
        }

        # Add API key if provided
        if api_key:
            llm_params["api_key"] = api_key

        # Add temperature and max_tokens if provided
        if params.get("temperature") is not None:
            llm_params["temperature"] = params["temperature"]
        if params.get("max_tokens") is not None:
            llm_params["max_tokens"] = params["max_tokens"]

        # Create LLM using LangChain's generic init_chat_model
        try:
            llm = init_chat_model(**llm_params)
        except ImportError as e:
            raise LLMError(
                f"Provider '{provider.provider_type}' not installed. "
                f"Run 'agentform init' to install required packages"
            ) from e
        except Exception as e:
            raise LLMError(
                f"Failed to initialize LLM for provider '{provider.provider_type}': {e}"
            ) from e

        self._llm_cache[cache_key] = llm
        self._logger.debug("llm_creation_complete", provider=provider_name, model=model)
        return llm

    def _schema_to_pydantic(self, schema: ResolvedSchema) -> type[BaseModel]:
        """Convert a ResolvedSchema to a Pydantic model.

        Args:
            schema: The schema to convert

        Returns:
            A dynamically created Pydantic model class
        """
        # Check cache first
        if schema.name in self._pydantic_model_cache:
            return self._pydantic_model_cache[schema.name]

        # Build field definitions for create_model
        field_definitions: dict[str, Any] = {}
        for field_name, field_def in schema.fields.items():
            if field_def.type == "list" and field_def.item_type:
                # List type
                item_type = _SCHEMA_TYPE_MAP.get(field_def.item_type, str)
                field_definitions[field_name] = (list[item_type], ...)  # type: ignore[valid-type]
            else:
                # Scalar type
                python_type = _SCHEMA_TYPE_MAP.get(field_def.type, str)
                field_definitions[field_name] = (python_type, ...)

        # Create the Pydantic model dynamically
        model_name = schema.name.title().replace("_", "")
        pydantic_model = create_model(model_name, **field_definitions)

        # Cache and return
        # create_model returns Any, but we know it's a BaseModel subclass
        typed_model = cast(type[BaseModel], pydantic_model)
        self._pydantic_model_cache[schema.name] = typed_model
        self._logger.debug(
            "pydantic_model_created",
            schema_name=schema.name,
            model_name=model_name,
            fields=list(field_definitions.keys()),
        )
        return typed_model

    async def execute(
        self,
        agent: ResolvedAgent,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an LLM call for an agent.

        Args:
            agent: Agent configuration
            input_data: Input data for the prompt

        Returns:
            Dict with 'response' and 'metadata' keys

        Raises:
            LLMError: If execution fails
        """
        self._logger.info(
            "llm_execution_start",
            agent_name=agent.name if hasattr(agent, "name") else "unknown",
            provider=agent.provider_name,
            model_preference=agent.model_preference,
            model_fallback=agent.model_fallback,
            has_instructions=bool(agent.instructions),
            input_keys=list(input_data.keys()) if input_data else [],
        )

        # Get params
        params = {}
        if agent.params:
            params = {
                "temperature": agent.params.temperature,
                "max_tokens": agent.params.max_tokens,
            }
            self._logger.debug("llm_params", params=params)

        # Try preferred model first, then fallback
        models_to_try = [agent.model_preference]
        if agent.model_fallback:
            models_to_try.append(agent.model_fallback)

        self._logger.debug("llm_models_to_try", models=models_to_try)

        last_error: Exception | None = None
        for model in models_to_try:
            try:
                self._logger.info("llm_model_attempt", model=model, provider=agent.provider_name)
                llm = self._get_llm(agent.provider_name, model, params)

                # Build messages
                messages: list[BaseMessage] = []
                if agent.instructions:
                    messages.append(SystemMessage(content=agent.instructions))
                    self._logger.debug(
                        "llm_system_message_added", instruction_length=len(agent.instructions)
                    )

                # Format input as user message
                if input_data:
                    import json

                    input_str = json.dumps(input_data, indent=2)
                    messages.append(HumanMessage(content=f"Input:\n{input_str}"))
                    self._logger.debug("llm_input_message_added", input_length=len(input_str))
                else:
                    messages.append(HumanMessage(content="Please proceed with your task."))
                    self._logger.debug("llm_empty_input_message_added")

                # Execute - check for structured output
                self._logger.debug("llm_invoke_start", model=model, message_count=len(messages))

                # Check if agent has output schema
                output_schema_name = getattr(agent, "output_schema_name", None)
                if output_schema_name and output_schema_name in self._schemas:
                    # Use structured output
                    schema = self._schemas[output_schema_name]
                    pydantic_model = self._schema_to_pydantic(schema)

                    self._logger.debug(
                        "llm_structured_output_enabled",
                        schema_name=output_schema_name,
                        model=model,
                    )

                    structured_llm = llm.with_structured_output(pydantic_model)
                    response = await structured_llm.ainvoke(messages)

                    # Convert Pydantic model to dict
                    response_data = response.model_dump()

                    self._logger.debug(
                        "llm_invoke_complete_structured",
                        model=model,
                        schema_name=output_schema_name,
                        response_keys=list(response_data.keys()),
                    )

                    usage = None  # Usage metadata not available for structured output
                    result = {
                        "response": response_data,
                        "model": model,
                        "provider": agent.provider_name,
                        "usage": usage,
                        "structured": True,
                        "schema_name": output_schema_name,
                    }
                else:
                    # Standard invocation
                    response = await llm.ainvoke(messages)
                    self._logger.debug(
                        "llm_invoke_complete",
                        model=model,
                        response_length=len(response.content) if response.content else 0,
                    )

                    usage = getattr(response, "usage_metadata", None)
                    result = {
                        "response": response.content,
                        "model": model,
                        "provider": agent.provider_name,
                        "usage": usage,
                    }

                self._logger.info(
                    "llm_execution_success",
                    model=model,
                    provider=agent.provider_name,
                    structured=output_schema_name is not None,
                )

                return result

            except Exception as e:
                self._logger.warning(
                    "llm_model_failed",
                    model=model,
                    provider=agent.provider_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                last_error = e
                continue

        self._logger.error(
            "llm_execution_failed_all_models",
            models_tried=models_to_try,
            last_error=str(last_error) if last_error else None,
            last_error_type=type(last_error).__name__ if last_error else None,
        )
        raise LLMError(f"All models failed. Last error: {last_error}")
