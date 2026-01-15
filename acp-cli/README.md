# ACP CLI

Command-line interface for running **Agent Control Protocol** workflows. Define AI agents and workflows in YAML, then run them with a single command.

## Installation

```bash
pip install acp-cli
```

**Requirements:** Python 3.12+

## Quick Start

### 1. Create an Agent Spec

Create a file called `agent.yaml`:

```yaml
version: "0.1"

project:
  name: my-assistant

providers:
  llm:
    openai:
      api_key: env:OPENAI_API_KEY

agents:
  - name: assistant
    provider: openai
    model:
      preference: gpt-4o-mini
    instructions: |
      You are a helpful assistant. Answer questions clearly and concisely.

workflows:
  - name: ask
    entry: process
    steps:
      - id: process
        type: llm
        agent: assistant
        input:
          question: $input.question
        save_as: answer
        next: end

      - id: end
        type: end
```

### 2. Set Your API Key

```bash
export OPENAI_API_KEY="your-api-key"
```

### 3. Run the Workflow

```bash
acp run ask --spec agent.yaml
```

The CLI will prompt you for any required inputs:

```
Running workflow: ask
Spec file: agent.yaml

✓ Specification compiled

Missing required inputs. Please provide them:

  question: What is the capital of France?

Executing workflow...

✓ Workflow completed

Output:
"The capital of France is Paris."
```

## Commands

### `acp validate`

Validate an ACP specification file without running it.

```bash
acp validate agent.yaml
```

**Options:**
- `--no-check-env` — Skip checking if environment variables are set

**Example output:**
```
Validating: agent.yaml

✓ YAML syntax valid
✓ Schema validation passed
✓ Validation passed

╭─ Specification Summary ─╮
│ Providers: openai       │
│ Agents: 1               │
│ Workflows: 1            │
╰─────────────────────────╯
```

### `acp run`

Run a workflow from an ACP specification.

```bash
acp run <workflow_name> [OPTIONS]
```

**Arguments:**
- `workflow_name` — Name of the workflow to run (required)

**Options:**
| Option | Short | Description |
|--------|-------|-------------|
| `--spec` | `-s` | Path to YAML spec file (default: `acp.yaml`) |
| `--input` | `-i` | JSON input data as string or `@file.json` |
| `--input-file` | `-f` | Path to JSON file with input data |
| `--output` | `-o` | Write output to file instead of stdout |
| `--trace` | `-t` | Write execution trace to file |
| `--verbose` | `-v` | Show verbose output |

**Examples:**

```bash
# Run with inline JSON input
acp run ask --spec agent.yaml --input '{"question": "Hello!"}'

# Run with input from file
acp run ask --spec agent.yaml --input-file input.json

# Run with @file syntax
acp run ask --spec agent.yaml --input @input.json

# Save output to file
acp run ask --spec agent.yaml --output result.json

# Verbose mode (shows detailed logs)
acp run ask --spec agent.yaml --verbose
```

## Input Handling

The CLI automatically detects required inputs by analyzing `$input.*` references in your workflow. If inputs are missing, it prompts you interactively:

```bash
$ acp run ask --spec agent.yaml

Missing required inputs. Please provide them:

  question: _
```

You can also provide partial inputs and be prompted for the rest:

```bash
$ acp run process --spec agent.yaml --input '{"name": "Alice"}'

Missing required inputs. Please provide them:

  age: _
```

## Environment Variables

API keys and secrets can be referenced from environment variables:

```yaml
providers:
  llm:
    openai:
      api_key: env:OPENAI_API_KEY
    anthropic:
      api_key: env:ANTHROPIC_API_KEY
```

The CLI validates that required environment variables are set before running.

## Example Agent

Here's a complete example with multiple agents and a more complex workflow:

```yaml
version: "0.1"

project:
  name: code-reviewer

providers:
  llm:
    openai:
      api_key: env:OPENAI_API_KEY

policies:
  - name: default
    budgets:
      max_cost_usd_per_run: 1.00
      timeout_seconds: 120

agents:
  - name: reviewer
    provider: openai
    model:
      preference: gpt-4o
    instructions: |
      You are an expert code reviewer. Analyze the provided code and give
      constructive feedback on:
      - Code quality and readability
      - Potential bugs or issues
      - Performance considerations
      - Best practices
    policy: default

workflows:
  - name: review
    entry: analyze
    steps:
      - id: analyze
        type: llm
        agent: reviewer
        input:
          code: $input.code
          language: $input.language
        save_as: review
        next: end

      - id: end
        type: end
```

Run it:

```bash
acp run review --spec code-reviewer.yaml --input '{
  "code": "def add(a, b): return a + b",
  "language": "python"
}'
```

## License

MIT
