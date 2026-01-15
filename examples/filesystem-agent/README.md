# Filesystem Agent Example

An ACP example demonstrating an agent that can read, write, and analyze files using the filesystem MCP server.

## Overview

This example showcases how to integrate external capabilities via MCP (Model Context Protocol) servers. The agent can interact with the filesystem to read files, write content, and list directories—all while operating within defined policies and budgets.

## Prerequisites

1. OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

## Usage

### Read and Summarize a File

```bash
acp run read_and_summarize --spec spec.yaml --input-file input.yaml
```

### List Directory Contents

```bash
acp run list_and_read --spec spec.yaml --input-json '{
  "directory_path": ".",
  "task": "Describe what files are present"
}'
```

### Write a File

```bash
acp run write_file --spec spec.yaml --input-json '{
  "file_path": "notes.txt",
  "instructions": "Write a brief note about AI assistants"
}'
```

## Spec File Structure

### `servers`
Define external MCP servers that provide capabilities. The filesystem server runs as a subprocess via stdio transport.

```yaml
servers:
  - name: filesystem
    type: mcp                        # Server type (MCP protocol)
    transport: stdio                 # Communication method
    command:                         # Command to start the server
      - npx
      - "@modelcontextprotocol/server-filesystem"
      - /path/to/allowed/directory   # Restrict access to this path
```

### `capabilities`
Map server methods to named capabilities with defined side effects. Side effects help the runtime understand what operations do.

```yaml
capabilities:
  - name: read_file
    server: filesystem               # Reference to server defined above
    method: read_file                # Method name on the MCP server
    side_effect: read                # Indicates read-only operation

  - name: write_file
    server: filesystem
    method: write_file
    side_effect: write               # Indicates state-changing operation

  - name: list_directory
    server: filesystem
    method: list_directory
    side_effect: read
```

### `policies`
More granular budgets for agents working with external capabilities.

```yaml
policies:
  - name: filesystem_policy
    budgets:
      max_cost_usd_per_run: 0.50     # Cost limit
      max_capability_calls: 20        # Limit external API calls
      timeout_seconds: 120            # Generous timeout for file operations
```

### `agents`
Agents reference capabilities in their `allow` list, determining what external actions they can take.

```yaml
agents:
  - name: file_assistant
    provider: openai
    model:
      preference: gpt-4o-mini
      fallback: gpt-4o
    instructions: |
      You are a helpful file assistant...
    allow:
      - read_file                    # Agent can use these capabilities
      - write_file
      - list_directory
    policy: filesystem_policy
```

### `workflows`
Multiple workflows demonstrate different use cases, each with their own entry points and step chains.

#### Read and Summarize Workflow
```yaml
- name: read_and_summarize
  entry: read
  steps:
    - id: read
      type: call                     # Capability call step
      capability: read_file          # Call this capability
      args:
        path: $input.file_path       # Pass input to capability
      save_as: file_content          # Store result
      next: summarize

    - id: summarize
      type: llm
      agent: file_assistant
      input:
        file_path: $input.file_path
        content: $state.file_content # Reference previous step's result
        task: $input.task
      save_as: summary
      next: end
```

## Input Schemas

### `read_and_summarize` Workflow
```yaml
file_path: "path/to/file.txt"
task: "Summarize this file"
```

### `list_and_read` Workflow
```yaml
directory_path: "."
task: "Describe the directory contents"
```

### `write_file` Workflow
```yaml
file_path: "output.txt"
instructions: "What content to generate"
```

## Key Concepts

### Capability Calls vs LLM Steps
- **`type: call`**: Directly invokes a capability (file operation, API call, etc.)
- **`type: llm`**: Sends input to an LLM agent for processing

### State Management
Results from each step are stored in the workflow state using `save_as`. Subsequent steps can reference these values with `$state.variable_name`.

### Side Effects
Capabilities declare their side effects (`read`, `write`) to help the runtime understand operation types. Write operations may require additional approval in some policies.

