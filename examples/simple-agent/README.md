# Simple Agent Example

A minimal ACP example demonstrating a basic LLM-powered agent that answers questions.

## Overview

This is the simplest possible ACP configuration—a single agent with no external capabilities. It showcases the core concepts of ACP specification without the complexity of MCP servers or multi-agent workflows.

## Prerequisites

- OpenAI API key set as environment variable:
  ```bash
  export OPENAI_API_KEY="your-api-key"
  ```

## Usage

Run the example with:

```bash
acp run ask --spec spec.yaml --input-file input.yaml
```

Or provide inline input:

```bash
acp run ask --spec spec.yaml --input-json '{"question": "What is the meaning of life?"}'
```

## Spec File Structure

### `version`
Specifies the ACP specification version being used.

```yaml
version: "0.1"
```

### `project`
Basic project metadata including the project name.

```yaml
project:
  name: simple-agent-example
```

### `providers`
Configures LLM providers. This example uses OpenAI with default parameters that apply to all agents using this provider.

```yaml
providers:
  llm:
    openai:
      api_key: env:OPENAI_API_KEY    # Reference environment variable
      default_params:
        temperature: 0.7              # Controls randomness (0-1)
        max_tokens: 2000              # Maximum response length
```

### `policies`
Define resource constraints and budgets for agent execution. Policies help prevent runaway costs and ensure predictable behavior.

```yaml
policies:
  - name: default
    budgets:
      max_cost_usd_per_run: 0.50    # Maximum cost per workflow run
      timeout_seconds: 60            # Maximum execution time
```

### `agents`
Configure individual agents with their models, instructions, and capabilities.

```yaml
agents:
  - name: assistant
    provider: openai                 # Reference to provider defined above
    model:
      preference: gpt-4o-mini        # Primary model choice
      fallback: gpt-4o               # Fallback if primary unavailable
    params:
      temperature: 0.5               # Override provider default
    instructions: |                  # System prompt for the agent
      You are a helpful assistant. Answer questions clearly and concisely.
      If you don't know something, say so.
    allow: []                        # No external capabilities needed
    policy: default                  # Apply the "default" policy
```

### `workflows`
Define the execution flow using steps. Each workflow has an entry point and a series of connected steps.

```yaml
workflows:
  - name: ask
    entry: process                   # Starting step ID
    steps:
      - id: process
        type: llm                    # Step that calls an LLM agent
        agent: assistant             # Reference to agent defined above
        input:
          question: $input.question  # Map workflow input to agent input
        save_as: answer              # Store result in state as "answer"
        next: end                    # Next step to execute

      - id: end
        type: end                    # Terminates the workflow
```

## Input Schema

The workflow expects input with the following structure:

```yaml
question: "Your question here"
```

## Output

The workflow produces output containing the agent's response, accessible via `$state.answer.response` in subsequent steps or returned as the final result.

