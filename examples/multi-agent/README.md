# Multi-Agent Example

An ACP example demonstrating multiple agents working together with conditional logic to route tasks appropriately.

## Overview

This example showcases advanced ACP features including:
- **Multiple LLM providers**: OpenAI and Anthropic working together
- **Agent specialization**: Different agents for different task complexities
- **Conditional routing**: Dynamic workflow paths based on classification results
- **Policy differentiation**: Fast vs. thorough processing with different budgets

## Prerequisites

1. OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

2. Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"
   ```

## Usage

Run with the provided input:

```bash
acp run smart_respond --spec spec.yaml --input-file input.yaml
```

Try different task complexities:

```bash
# Simple task (routed to quick_responder)
acp run smart_respond --spec spec.yaml --input-json '{"task": "What is 2+2?"}'

# Complex task (routed to deep_analyst)
acp run smart_respond --spec spec.yaml --input-json '{"task": "Analyze the pros and cons of remote work policies"}'
```

## Spec File Structure

### Multiple Providers
Configure different LLM providers, each with their own authentication and default parameters.

```yaml
providers:
  llm:
    openai:
      api_key: env:OPENAI_API_KEY
      default_params:
        temperature: 0.7
        max_tokens: 2000
    anthropic:
      api_key: env:ANTHROPIC_API_KEY
      default_params:
        temperature: 0.5
        max_tokens: 4000
```

### Differentiated Policies
Different policies for different use cases—fast and cheap vs. thorough and expensive.

```yaml
policies:
  - name: fast
    budgets:
      max_cost_usd_per_run: 0.10     # Low budget for quick tasks
      timeout_seconds: 30             # Short timeout

  - name: thorough
    budgets:
      max_cost_usd_per_run: 1.00     # Higher budget for analysis
      timeout_seconds: 120            # Longer timeout allowed
```

### Specialized Agents
Each agent has a specific role with tailored instructions and configurations.

```yaml
agents:
  # Classifier: Quickly categorizes incoming tasks
  - name: classifier
    provider: openai
    model:
      preference: gpt-4o-mini         # Fast, cheap model
    params:
      temperature: 0.1                # Low temperature for consistency
    instructions: |
      You are a task classifier. Analyze the input and classify it.
      Categories:
      - "simple": Basic questions, greetings, simple tasks
      - "complex": Research, analysis, multi-step tasks
      Respond with ONLY the category name, nothing else.
    allow: []
    policy: fast

  # Quick Responder: Handles simple tasks efficiently
  - name: quick_responder
    provider: openai
    model:
      preference: gpt-4o-mini
    instructions: |
      You are a quick assistant. Give brief, helpful responses.
    policy: fast

  # Deep Analyst: Thorough analysis using Claude
  - name: deep_analyst
    provider: anthropic              # Different provider
    model:
      preference: claude-sonnet-4-5-20250929
    params:
      temperature: 0.3
      max_tokens: 4000
    instructions: |
      You are a thorough analyst. Provide detailed responses.
      Structure with: Summary, Analysis, Recommendations.
    policy: thorough
```

### Conditional Workflow
The workflow uses conditions to route tasks to the appropriate agent.

```yaml
workflows:
  - name: smart_respond
    entry: classify
    steps:
      # Step 1: Classify the task
      - id: classify
        type: llm
        agent: classifier
        input:
          task: $input.task
        save_as: classification
        next: route

      # Step 2: Route based on classification
      - id: route
        type: condition
        condition: $state.classification.response == "simple"
        on_true: quick_response       # Go here if simple
        on_false: deep_response       # Go here if complex

      # Step 3a: Quick response path
      - id: quick_response
        type: llm
        agent: quick_responder
        input:
          task: $input.task
        save_as: response
        next: end

      # Step 3b: Deep analysis path
      - id: deep_response
        type: llm
        agent: deep_analyst
        input:
          task: $input.task
        save_as: response
        next: end

      - id: end
        type: end
```

## Input Schema

```yaml
task: "Your task or question here"
```

## Key Concepts

### Conditional Routing
The `condition` step type allows dynamic workflow paths:

```yaml
- id: route
  type: condition
  condition: $state.classification.response == "simple"
  on_true: quick_response
  on_false: deep_response
```

Conditions evaluate expressions against the current state and route to different steps.

### Multi-Provider Strategy
Using multiple providers allows you to:
- **Optimize costs**: Use cheaper models for simple tasks
- **Leverage strengths**: Different models excel at different tasks
- **Build resilience**: Fallback options when one provider is unavailable

### Agent Specialization
Specialized agents with focused instructions tend to perform better than general-purpose agents. The classifier has very specific instructions to output only category names, making its output predictable and easy to use in conditions.

### Policy-Based Budgeting
Different policies for different agents ensure appropriate resource allocation:
- Classifiers get minimal budgets (they just need to output one word)
- Analysts get larger budgets for detailed work
- Timeouts match expected task complexity

