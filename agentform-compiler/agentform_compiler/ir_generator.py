"""IR (Intermediate Representation) generation from validated specs."""

import re
from typing import TYPE_CHECKING

from agentform_compiler.credentials import get_env_var_name, resolve_env_var
from agentform_schema.ir import (
    CompiledSpec,
    ResolvedAgent,
    ResolvedCapability,
    ResolvedCredential,
    ResolvedPolicy,
    ResolvedProvider,
    ResolvedSchema,
    ResolvedServer,
    ResolvedStep,
    ResolvedWorkflow,
    SchemaField,
)
from agentform_schema.models import (
    BudgetConfig,
    LLMProviderParams,
    SpecRoot,
)

if TYPE_CHECKING:
    from agentform_compiler.agentform_ast import AgentformFile

# Regex for list(T) type syntax
_LIST_TYPE_PATTERN = re.compile(r"^list\((\w+)\)$")


class IRGenerationError(Exception):
    """Error during IR generation."""

    pass


def _parse_schema_field_type(type_str: str) -> SchemaField:
    """Parse a schema field type string into a SchemaField.

    Args:
        type_str: Type string (e.g., "string", "number", "list(string)")

    Returns:
        SchemaField with type and optional item_type
    """
    # Check for list(T) type
    list_match = _LIST_TYPE_PATTERN.match(type_str)
    if list_match:
        item_type = list_match.group(1)
        return SchemaField(type="list", item_type=item_type)

    # Scalar type
    return SchemaField(type=type_str)


def _generate_schemas(agentform_file: "AgentformFile") -> dict[str, ResolvedSchema]:
    """Generate resolved schemas from AST.

    Args:
        agentform_file: Parsed AST

    Returns:
        Dict of schema name to ResolvedSchema
    """
    schemas: dict[str, ResolvedSchema] = {}

    for schema_block in agentform_file.schemas:
        fields: dict[str, SchemaField] = {}
        for attr in schema_block.attributes:
            if isinstance(attr.value, str):
                fields[attr.name] = _parse_schema_field_type(attr.value)

        schemas[schema_block.name] = ResolvedSchema(
            name=schema_block.name,
            fields=fields,
        )

    return schemas


def _get_agent_output_schema(
    agentform_file: "AgentformFile",
    agent_name: str,
) -> str | None:
    """Get the output_schema name for an agent from the AST.

    Args:
        agentform_file: Parsed AST
        agent_name: Name of the agent

    Returns:
        Schema name if output_schema is set, None otherwise
    """
    from agentform_compiler.agentform_ast import Reference

    agent_block = agentform_file.get_agent(agent_name)
    if agent_block is None:
        return None

    output_schema = agent_block.get_attribute("output_schema")
    # Reference is like schema.person -> extract "person"
    if (
        isinstance(output_schema, Reference)
        and output_schema.parts[0] == "schema"
        and len(output_schema.parts) >= 2
    ):
        return output_schema.parts[1]

    return None


def generate_ir(
    spec: SpecRoot,
    resolve_credentials: bool = True,
    agentform_file: "AgentformFile | None" = None,
) -> CompiledSpec:
    """Generate IR from a validated specification.

    Args:
        spec: Validated specification
        resolve_credentials: Whether to resolve env vars to actual values
        agentform_file: Optional AST for extracting schemas and output_schema refs

    Returns:
        Compiled specification (IR)

    Raises:
        IRGenerationError: If IR generation fails
    """
    # Generate schemas from AST if provided
    schemas: dict[str, ResolvedSchema] = {}
    if agentform_file is not None:
        schemas = _generate_schemas(agentform_file)

    # Resolve providers
    providers: dict[str, ResolvedProvider] = {}
    for name, provider in spec.providers.llm.items():
        var_name = get_env_var_name(provider.api_key)

        if var_name:
            # env:VAR_NAME format - resolve from environment
            value = None
            if resolve_credentials:
                value = resolve_env_var(provider.api_key, required=False)
            api_key = ResolvedCredential(env_var=var_name, value=value)
        else:
            # Direct value (from variable substitution)
            api_key = ResolvedCredential(env_var="DIRECT_VALUE", value=provider.api_key)

        # Extract provider_type from name
        # Name format is either "{vendor}" or "{vendor}_{name}"
        # Provider type is the vendor part (before first underscore, or whole name if no underscore)
        provider_type = name.split("_")[0] if "_" in name else name

        providers[name] = ResolvedProvider(
            name=name,
            provider_type=provider_type,
            api_key=api_key,
            default_params=provider.default_params or LLMProviderParams(),
        )

    # Resolve servers
    servers: dict[str, ResolvedServer] = {}
    for server in spec.servers:
        auth_token = None
        if server.auth and server.auth.token:
            var_name = get_env_var_name(server.auth.token)
            if var_name:
                # env:VAR_NAME format
                value = None
                if resolve_credentials:
                    value = resolve_env_var(server.auth.token, required=False)
                auth_token = ResolvedCredential(env_var=var_name, value=value)
            else:
                # Direct value (from variable substitution)
                auth_token = ResolvedCredential(env_var="DIRECT_VALUE", value=server.auth.token)

        servers[server.name] = ResolvedServer(
            name=server.name,
            command=server.command,
            auth_token=auth_token,
        )

    # Resolve capabilities (method schemas will be populated by MCP discovery)
    capabilities: dict[str, ResolvedCapability] = {}
    for cap in spec.capabilities:
        capabilities[cap.name] = ResolvedCapability(
            name=cap.name,
            server_name=cap.server,
            method_name=cap.method,
            method_schema=None,  # Populated during MCP resolution
            side_effect=cap.side_effect,
            requires_approval=cap.requires_approval,
        )

    # Resolve policies
    policies: dict[str, ResolvedPolicy] = {}
    for policy in spec.policies:
        policies[policy.name] = ResolvedPolicy(
            name=policy.name,
            budgets=policy.budgets or BudgetConfig(),
        )

    # Resolve agents
    agents: dict[str, ResolvedAgent] = {}
    for agent in spec.agents:
        # Merge provider defaults with agent params
        resolved_provider = providers.get(agent.provider)
        if resolved_provider is None:
            raise IRGenerationError(
                f"Provider '{agent.provider}' not found for agent '{agent.name}'"
            )

        merged_params = LLMProviderParams()
        if resolved_provider.default_params:
            merged_params = resolved_provider.default_params.model_copy()
        if agent.params:
            # Override with agent-specific params
            for field_name in type(agent.params).model_fields:
                agent_value = getattr(agent.params, field_name)
                if agent_value is not None:
                    setattr(merged_params, field_name, agent_value)

        # Get output_schema from AST if available
        output_schema_name = None
        if agentform_file is not None:
            output_schema_name = _get_agent_output_schema(agentform_file, agent.name)

        agents[agent.name] = ResolvedAgent(
            name=agent.name,
            provider_name=agent.provider,
            model_preference=agent.model.preference,
            model_fallback=agent.model.fallback,
            params=merged_params,
            instructions=agent.instructions,
            allowed_capabilities=agent.allow,
            policy_name=agent.policy,
            output_schema_name=output_schema_name,
        )

    # Resolve workflows
    workflows: dict[str, ResolvedWorkflow] = {}
    for workflow in spec.workflows:
        steps: dict[str, ResolvedStep] = {}
        for step in workflow.steps:
            resolved_step = ResolvedStep(
                id=step.id,
                type=step.type,
                agent_name=step.agent,
                input_mapping=step.input,
                capability_name=step.capability,
                args_mapping=step.args,
                condition_expr=step.condition,
                on_true_step=step.on_true,
                on_false_step=step.on_false,
                payload_expr=step.payload,
                on_approve_step=step.on_approve,
                on_reject_step=step.on_reject,
                save_as=step.save_as,
                next_step=step.next,
            )
            steps[step.id] = resolved_step

        workflows[workflow.name] = ResolvedWorkflow(
            name=workflow.name,
            entry_step=workflow.entry,
            steps=steps,
        )

    return CompiledSpec(
        version=spec.version,
        project_name=spec.project.name,
        providers=providers,
        servers=servers,
        capabilities=capabilities,
        policies=policies,
        schemas=schemas,
        agents=agents,
        workflows=workflows,
    )
