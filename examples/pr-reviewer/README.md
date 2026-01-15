# PR Reviewer Example

An ACP example demonstrating an automated pull request reviewer using the GitHub MCP server with human approval gates.

## Overview

This example showcases advanced ACP features including:
- **GitHub integration**: Fetch PR data and submit reviews via MCP
- **Human-in-the-loop**: Approval gates before submitting reviews
- **Write operations with approval**: Capabilities that require explicit approval
- **Multi-step data gathering**: Sequential capability calls to build context

## Prerequisites

1. OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

2. GitHub Personal Access Token with appropriate permissions:
   ```bash
   export GITHUB_PERSONAL_ACCESS_TOKEN="your-github-token"
   ```
   
   Required token scopes:
   - `repo` (for private repositories)
   - `public_repo` (for public repositories only)

3. Node.js and npm (for the MCP GitHub server):
   ```bash
   npm install -g @modelcontextprotocol/server-github
   ```

## Usage

Review a pull request:

```bash
acp run review_pr --spec spec.yaml --input-file input.yaml
```

Or specify PR details inline:

```bash
acp run review_pr --spec spec.yaml --input-json '{
  "owner": "myorg",
  "repo": "myrepo",
  "pr_number": 42
}'
```

The workflow will:
1. Fetch PR metadata
2. Fetch changed files
3. Generate a review using GPT-4
4. **Pause for your approval**
5. Submit the review to GitHub (only if approved)

## Spec File Structure

### Authenticated MCP Server
GitHub server requires authentication via environment variable.

```yaml
servers:
  - name: github
    type: mcp
    transport: stdio
    command:
      - npx
      - "@modelcontextprotocol/server-github"
    auth:
      token: env:GITHUB_PERSONAL_ACCESS_TOKEN  # Auth token from env
```

### Capabilities with Approval Requirements
Some capabilities modify state and require explicit human approval.

```yaml
capabilities:
  # Read-only capabilities
  - name: get_pr
    server: github
    method: get_pull_request
    side_effect: read

  - name: list_pr_files
    server: github
    method: get_pull_request_files
    side_effect: read

  # Write capability requiring approval
  - name: create_review
    server: github
    method: create_pull_request_review
    side_effect: write
    requires_approval: true           # Human must approve before execution
```

### Expert Reviewer Agent
Specialized agent with detailed code review instructions.

```yaml
agents:
  - name: reviewer
    provider: openai
    model:
      preference: gpt-4o              # Using capable model for code review
    params:
      temperature: 0.2                # Low temperature for consistent reviews
    instructions: |
      You are an expert code reviewer. Review pull requests thoroughly.
      
      Focus on:
      - Code quality and best practices
      - Potential bugs or edge cases
      - Performance implications
      - Security concerns
      - Documentation and readability
      
      Be constructive and specific in your feedback.
      Suggest improvements where possible.
    allow:
      - get_pr
      - list_pr_files
      - create_review
    policy: review_policy
```

### Workflow with Human Approval
The workflow includes a human approval step before submitting reviews.

```yaml
workflows:
  - name: review_pr
    entry: fetch_pr
    steps:
      # Step 1: Fetch PR metadata
      - id: fetch_pr
        type: call
        capability: get_pr
        args:
          owner: $input.owner
          repo: $input.repo
          pull_number: $input.pr_number
        save_as: pr_data
        next: fetch_files

      # Step 2: Fetch changed files
      - id: fetch_files
        type: call
        capability: list_pr_files
        args:
          owner: $input.owner
          repo: $input.repo
          pull_number: $input.pr_number
        save_as: pr_files
        next: analyze

      # Step 3: Generate review with LLM
      - id: analyze
        type: llm
        agent: reviewer
        input:
          pr: $state.pr_data
          files: $state.pr_files
        save_as: review
        next: approval

      # Step 4: Human approval gate
      - id: approval
        type: human_approval
        payload: $state.review        # Show this to the human
        on_approve: submit_review     # If approved, continue
        on_reject: end                # If rejected, stop

      # Step 5: Submit the review
      - id: submit_review
        type: call
        capability: create_review
        args:
          owner: $input.owner
          repo: $input.repo
          pull_number: $input.pr_number
          body: $state.review.response
          event: COMMENT              # COMMENT, APPROVE, or REQUEST_CHANGES
        save_as: result
        next: end

      - id: end
        type: end
```

## Input Schema

```yaml
owner: "organization-or-username"
repo: "repository-name"
pr_number: 123
```

## Key Concepts

### Human Approval Gates
The `human_approval` step type pauses workflow execution and waits for human input:

```yaml
- id: approval
  type: human_approval
  payload: $state.review          # Data to show the approver
  on_approve: submit_review       # Next step if approved
  on_reject: end                  # Next step if rejected
```

This ensures humans remain in control of consequential actions.

### Capability Approval
Capabilities marked with `requires_approval: true` trigger approval prompts even during LLM agent tool use:

```yaml
- name: create_review
  server: github
  method: create_pull_request_review
  side_effect: write
  requires_approval: true
```

### Sequential Data Gathering
The workflow demonstrates gathering data across multiple capability calls before processing:
1. `fetch_pr` → gets PR title, description, author, etc.
2. `fetch_files` → gets list of changed files with diffs
3. `analyze` → LLM reviews with all context

### Review Event Types
When submitting reviews, the `event` parameter controls the review type:
- `COMMENT`: General feedback without approval/rejection
- `APPROVE`: Approve the PR
- `REQUEST_CHANGES`: Request changes before merge

## Safety Considerations

This example demonstrates multiple safety layers:

1. **Policy budgets**: Cost and time limits prevent runaway execution
2. **Capability approval**: Write operations require explicit approval
3. **Human approval step**: Final review before submitting to GitHub
4. **Read-first pattern**: Gather data with read operations, then review before writing

These patterns ensure the agent cannot take irreversible actions without human oversight.

