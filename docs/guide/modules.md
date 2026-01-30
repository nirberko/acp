# Agentform Modules

Agentform supports a **Terraform-style module system** for creating reusable, shareable agent configurations. Modules let you package providers, policies, agents, and workflows together, making it easy for others to use without extensive configuration.

## Using Modules

### 1. Import a module in your project

Create a module block referencing a Git repository:

```hcl
module "pr-reviewer" {
  source  = "github.com/org/agentform-modules//pr-reviewer"
  version = "v1.0.0"  // Git branch, tag, or commit
  
  // Pass required parameters
  api_key = var.openai_api_key
  model   = "gpt-4o"
}
```

The `//` syntax separates the repository URL from the subdirectory path (like Terraform).

### 2. Initialize your project

Download all external modules to your local `.af/modules/` directory:

```bash
agentform init
```

This clones the module repositories locally. You must run `agentform init` before compiling or running workflows that use external modules.

### 3. Use module resources

Resources from modules are namespaced with `module.<name>`:

```hcl
workflow "review" {
  entry = step.start
  
  step "start" {
    type  = "llm"
    agent = agent.module.pr-reviewer.reviewer  // Use module's agent
    next  = step.end
  }
  
  step "end" { type = "end" }
}
```

Or run a module's workflow directly:

```bash
agentform run module.pr-reviewer.review_workflow .
```

## Creating Modules

A module is simply a directory containing `.af` files. To create a shareable module:

### 1. Create the module structure

```
my-module/
├── 00-project.af      # Module metadata
├── 01-variables.af    # Input parameters (variables)
├── 02-providers.af    # LLM providers
├── 03-policies.af     # Policies
├── 04-models.af       # Model configurations
├── 05-agents.af       # Agent definitions
└── 06-workflows.af    # Workflows (optional)
```

### 2. Define input variables

Variables without defaults become required parameters:

```hcl
// 01-variables.af
variable "api_key" {
  type        = string
  description = "API key for the LLM provider"
  sensitive   = true
  // No default = required parameter
}

variable "model" {
  type        = string
  description = "Model to use"
  default     = "gpt-4o-mini"  // Has default = optional
}
```

### 3. Publish to Git

Push your module to a Git repository. Users can then reference it:

```hcl
module "my-module" {
  source  = "github.com/your-org/your-repo//path/to/module"
  version = "main"
  
  api_key = var.my_api_key
}
```

## Module Source Formats

| Format | Example |
|--------|---------|
| GitHub | `github.com/org/repo` |
| GitHub with subdirectory | `github.com/org/repo//modules/my-module` |
| GitLab | `gitlab.com/org/repo` |
| Local path | `./modules/my-module` |

## Module Caching

Modules are cached in `.af/modules/` within your project directory:

```
my-project/
├── .af/
│   └── modules/
│       └── github_com_org_repo_abc123/  # Cached module
├── 00-project.af
└── 01-modules.af
```

Add `.af/` to your `.gitignore` - these are downloaded dependencies.

## Module Best Practices

When creating reusable modules, follow these guidelines to make them reliable and easy for others to adopt:

### Version control

- Commit all module source files (`.af` and supporting files) to a Git repository.
- Do **not** commit the `.af/modules/` cache directory – treat it like any other build artifact.
- Use tags or version branches (e.g., `v1.0.0`) so users can pin a specific module version.

### Documentation

- Include a `README.md` in the module root that explains:
  - What the module does.
  - Required and optional input variables.
  - Any external dependencies (APIs, credentials, tools).
  - Example usage showing a `module` block and how to call its workflows or agents.
- Use `description` fields on variables, agents, and workflows to make the module self-describing.

### Defaults and configuration

- Provide sensible defaults for non-sensitive, non-environment-specific values to make modules easy to adopt.
- Omit `default` for values that must be explicitly provided (like API keys) so they are clearly required.
- Keep variable names stable across versions; if you must change them, document the migration path.

### Testing

- Create one or more example workflows in the module that exercise the main behavior end to end.
- Test modules locally before publishing by:
  - Running `agentform init` against a consuming project.
  - Executing key workflows (`agentform run module.<name>.<workflow> .`).
- When possible, pin provider models or critical settings so behavior is consistent across environments.

### Naming conventions

- Use clear, descriptive module names (e.g., `pr-reviewer`, `code-audit`, `data-enrichment`).
- Keep file ordering predictable (e.g., `00-project.af`, `01-variables.af`, `02-providers.af`, …) so users can navigate easily.
- Avoid breaking changes to exported names (agents, workflows, variables). If a breaking change is unavoidable, publish it under a new major version or a new module name.
