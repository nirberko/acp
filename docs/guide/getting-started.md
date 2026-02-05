# Getting Started

This guide will help you get up and running with Agentform in minutes.

## Installation

### Quick Install

```bash
pip install agentform-cli
```

### Verify Installation

```bash
agentform --help
```

## Prerequisites

- Python 3.12 or higher
- An API key for at least one LLM provider (OpenAI, Anthropic, etc.)

## Your First Agent

Let's create a simple agent that can answer questions.

### 1. Set up your API key

```bash
export OPENAI_API_KEY="your-openai-key"
```

### 2. Create an agent spec

Create a file called `my-agent.af`:

```hcl
agentform {
  version = "0.1"
  project = "my-first-agent"
}

variable "openai_api_key" {
  type        = string
  description = "OpenAI API key"
  sensitive   = true
}

provider "llm.openai" "default" {
  api_key = var.openai_api_key
  default_params {
    temperature = 0.7
    max_tokens  = 2000
  }
}

policy "default" {
  budgets {
    max_cost_usd_per_run = 0.50
    timeout_seconds      = 60
  }
}

model "gpt4o_mini" {
  provider = provider.llm.openai.default
  id       = "gpt-4o-mini"
}

model "gpt35" {
  provider = provider.llm.openai.default
  id       = "gpt-3.5-turbo"
}

agent "assistant" {
  model           = model.gpt4o_mini
  fallback_models = [model.gpt35]
  instructions    = "You are a helpful assistant. Answer questions clearly and concisely."
  policy          = policy.default
}

workflow "ask" {
  entry = step.process

  step "process" {
    type  = "llm"
    agent = agent.assistant
    input { question = input.question }
    output "answer" { from = result.text }
    next = step.end
  }

  step "end" { type = "end" }
}
```

### 3. Run it

Validate your spec:
```bash
agentform validate my-agent.af --var openai_api_key=$OPENAI_API_KEY
```

Run the workflow:
```bash
agentform run ask \
  --spec my-agent.af \
  --var openai_api_key=$OPENAI_API_KEY \
  --input '{"question": "What is the capital of France?"}'
```

You should see the agent's response!

## Understanding the Configuration

Let's break down what we just created:

### `agentform` block
Defines the project metadata and version.

### `variable` block
Declares input variables. The `sensitive = true` flag ensures the value isn't logged.

### `provider` block
Configures the LLM provider (OpenAI in this case) with your API key and default parameters.

### `policy` block
Sets budgets and limits for agent execution:
- `max_cost_usd_per_run`: Maximum cost per workflow run
- `timeout_seconds`: Maximum execution time

### `model` block
Defines specific models from your provider. You can reference multiple models.

### `agent` block
Creates an agent with:
- A primary model (`model.gpt4o_mini`)
- Fallback models if the primary fails
- Instructions that define the agent's behavior
- A policy for resource limits

### `workflow` block
Defines the execution flow:
- `entry`: The starting step
- `step`: Individual workflow steps
  - `type = "llm"`: Uses an LLM agent
  - `input`: Maps input data
  - `output`: Extracts results
  - `next`: The next step in the flow

## Next Steps

- Explore the [Examples](../examples/index.md) to see more complex configurations
- Learn about [Modules](modules.md) for reusable agent configurations
- Check the [CLI Reference](../reference/cli.md) for all available commands
