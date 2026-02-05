# Introduction

**Agentform™** allows you to define AI agent systems declaratively using a native schema. Think *Infrastructure as Code*, but for AI agents.

## Why Agentform?

Most AI agent frameworks require you to write imperative code - managing state, handling retries, wiring up tools. Agentform takes a different approach: **describe your agents declaratively in Agentform native schema, and let the runtime engine handle the rest.**

```hcl
agent "reviewer" {
  model        = model.gpt4o
  instructions = "Review code for security issues"
  allow        = [capability.read_file, capability.get_diff]
  policy       = policy.strict
}
```

**The result:** Your agent configurations become version-controlled artifacts that are easy to review, share, and reproduce. The native `.af` format provides type safety, explicit references, and improved editor support.

## Key Features

- **Native Schema**: Define agents, workflows, and policies in type-safe `.af` format.
- **Modules**: Terraform-style reusable modules for sharing agent configurations via Git.
- **Multi-Provider**: Support for major LLM providers.
- **Multi-Agent**: Coordinate multiple specialized agents with conditional routing.
- **Security**: Built-in policy enforcement and human-in-the-loop approval.
