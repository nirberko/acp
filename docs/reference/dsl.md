# DSL Reference

Agentform uses a declarative schema inspired by HCL (HashiCorp Configuration Language) to define agents, workflows, and policies.

## Block Hierarchy

- `agentform`: Project metadata
- `variable`: Input parameters
- `provider`: Configures external services (LLMs)
- `server`: Configures MCP servers for tools
- `policy`: Defines execution limits and budgets
- `model`: Instantiates specific LLM models
- `capability`: Defines available tools/functions
- `agent`: Defines AI agents utilizing models and policies
- `workflow`: Orchestrates steps and execution flow
- `module`: Imports external configurations

---

## Blocks

### `agentform`

Defining project metadata.

```hcl
agentform {
  version = "0.1"
  project = "my-project"
}
```

**Arguments:**
- `version` (string, required): Schema version (e.g., "0.1").
- `project` (string, required): Unique project identifier.

---

### `variable`

Input variables for the configuration.

```hcl
variable "api_key" {
  type        = string
  description = "API key"
  sensitive   = true
  default     = "default-value"
}
```

**Arguments:**
- `type` (string, required): Data type (`string`, `number`, `bool`, `list`, `map`).
- `description` (string, optional): Documentation for the variable.
- `default` (any, optional): Default value if not provided.
- `sensitive` (bool, optional): If `true`, value is redacted in logs.

---

### `provider`

Configure an external service provider (e.g., LLM, Vector DB).

```hcl
provider "llm.openai" "default" {
  api_key = var.api_key
  default_params {
    temperature = 0.7
  }
}
```

**Types:**
- `llm.openai`
- `llm.anthropic`
- `llm.google`

**Arguments:**
- `api_key` (string, required): Authentication credential.
- `default_params` (block, optional): Default parameters for models using this provider.

---

### `server`

Configures a Model Context Protocol (MCP) server for external tools.

```hcl
server "filesystem" {
  command = "npx"
  args    = ["-y", "@modelcontextprotocol/server-filesystem", "."]
  env = {
    NODE_ENV = "production"
  }
}
```

**Arguments:**
- `command` (string, required): Executable to run.
- `args` (list of strings, optional): Arguments to pass to the command.
- `env` (map, optional): Environment variables for the process.

---

### `policy`

Defines execution boundaries, budgets, and safety limits.

```hcl
policy "standard" {
  budgets {
    max_cost_usd_per_run = 1.0
    timeout_seconds      = 300
    max_capability_calls = 50
  }
}
```

**Arguments:**
- `budgets` (block):
  - `max_cost_usd_per_run` (number)
  - `timeout_seconds` (number)
  - `max_steps` (number)
  - `max_capability_calls` (number)

---

### `model`

Define a model instance referencing a provider.

```hcl
model "gpt4" {
  provider = provider.llm.openai.default
  id       = "gpt-4-turbo"
}
```

**Arguments:**
- `provider` (reference, required): Reference to a defined provider.
- `id` (string, required): The provider-specific model ID (e.g., `gpt-4`, `claude-3-opus`).

---

### `capability`

Defines a tool or function available to agents.

```hcl
capability "read_file" {
  server    = server.filesystem
  method    = "tools/call"
  
  params {
    name = "read_file"
  }

  requires_approval = false
}
```

**Arguments:**
- `server` (reference, required): Reference to an MCP server.
- `method` (string, required): MCP method to call.
- `requires_approval` (bool, optional): If `true`, human approval is required before execution.

---

### `agent`

Define an AI agent.

```hcl
agent "helper" {
  model           = model.gpt4
  fallback_models = [model.gpt35]
  instructions    = "You are a helpful assistant."
  policy          = policy.standard
  
  capabilities = [
    capability.read_file
  ]
}
```

**Arguments:**
- `model` (reference, required): Primary model to use.
- `fallback_models` (list of references, optional): Models to try if primary fails.
- `instructions` (string, required): System prompt/persona.
- `policy` (reference, optional): Policy to enforce.
- `capabilities` (list of references, optional): Tools available to the agent.

---

### `workflow`

Define a multi-step execution flow.

```hcl
workflow "main" {
  entry = step.start
  
  step "start" {
    type  = "llm"
    agent = agent.helper
    input { query = input.query }
    next  = step.end
  }

  step "end" { type = "end" }
}
```

**Arguments:**
- `entry` (reference, required): The starting step.
- `step` (block, multiple): Defines a unit of work.

#### Step Types

**1. `llm`**
Invokes an agent.
- `agent` (reference): The agent to call.
- `input` (map): Input variables.
- `output` (map): Map results to variables.
- `next` (reference): Next step.

**2. `tool` / `call`**
Directly calls a capability.
- `capability` (reference): Tool to execute.
- `args` (map): Arguments for the tool.

**3. `condition`**
Branches logic based on variables.
- `condition` (string): Expression to evaluate.
- `if_true` (reference): Next step if true.
- `if_false` (reference): Next step if false.

**4. `wait` / `human_approval`**
Pauses execution for user input.

**5. `end`**
Terminates the workflow.

---

### `module`

Imports external configurations from a local path or Git repository.

```hcl
module "review_system" {
  source  = "github.com/agentform/modules//pr-reviewer"
  version = "v1.0.0"
  
  api_key = var.api_key
}
```

**Arguments:**
- `source` (string, required): URI of the module.
- `version` (string, optional): Git tag/branch.
- `*` (any): Inputs required by the module's variables.
