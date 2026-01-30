---
hide:
  - navigation
  - toc
---

<div class="hero-section">
  <h1>Agentform</h1>
  <p class="tagline">Define AI agent systems declaratively.<br>Infrastructure as Code for the AI Era.</p>

  <div class="hero-buttons">
    <a class="md-button md-button--primary" href="guide/getting-started/">Get Started</a>
    <a class="md-button" href="examples/">View Examples</a>
  </div>
</div>


-   :material-file-code:
    **Native Schema**
    Define complex agent behaviors, workflows, and policies in a type-safe, readable `.af` syntax.

-   :material-brain:
    **Multi-Provider**
    Seamlessly switch between OpenAI, Anthropic, and open-source models without rewriting code.

-   :material-connection:
    **MCP First**
    First-class support for the Model Context Protocol to connect agents with your data and tools.

-   :material-security:
    **Enterprise Safety**
    Enforce granular policies, budget limits, and human-in-the-loop approval gates.

-   :material-chart-timeline-variant:
    **Full Observability**
    Trace every step of your agent's execution with built-in logging and debugging tools.

-   :material-share-variant:
    **Modular & Reusable**
    Share agent configurations via Git-based modules, just like Terraform.


<div style="margin-top: 4rem;"></div>

## How It Works

<div style="margin: 4rem auto; max-width: 800px;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" style="background-color: transparent; width: 100%; height: auto;">
  <style>
    .node { fill: #1e293b; stroke: #6366f1; stroke-width: 2px; }
    .node-text { fill: #e2e8f0; font-family: sans-serif; font-size: 14px; text-anchor: middle; dominant-baseline: middle; }
    .edge { stroke: #94a3b8; stroke-width: 2px; fill: none; }
    .arrow { fill: #94a3b8; }
  </style>
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" class="arrow" />
    </marker>
  </defs>
  <rect x="50" y="180" width="120" height="50" rx="8" class="node" />
  <text x="110" y="205" class="node-text">User Request</text>
  <rect x="230" y="180" width="140" height="50" rx="8" class="node" />
  <text x="300" y="205" class="node-text">Form Controller</text>
  <polygon points="450,180 500,205 450,230 400,205" class="node" />
  <text x="450" y="205" class="node-text">Router</text>
  <rect x="550" y="100" width="120" height="50" rx="8" class="node" style="stroke: #ec4899;" />
  <text x="610" y="125" class="node-text">Action Agent</text>
  <rect x="550" y="300" width="120" height="50" rx="8" class="node" style="stroke: #a855f7;" />
  <text x="610" y="325" class="node-text">Planning Agent</text>
  <rect x="700" y="205" width="80" height="40" rx="20" class="node" style="fill: #22c55e; stroke: none;" />
  <text x="740" y="225" class="node-text" style="fill: #fff; font-weight: bold;">Result</text>
  <line x1="170" y1="205" x2="220" y2="205" class="edge" marker-end="url(#arrowhead)" />
  <line x1="370" y1="205" x2="390" y2="205" class="edge" marker-end="url(#arrowhead)" />
  <path d="M450,180 Q450,125 540,125" class="edge" marker-end="url(#arrowhead)" />
  <path d="M450,230 Q450,325 540,325" class="edge" marker-end="url(#arrowhead)" />
  <path d="M670,125 Q740,125 740,195" class="edge" marker-end="url(#arrowhead)" />
  <path d="M670,325 Q740,325 740,255" class="edge" marker-end="url(#arrowhead)" />
</svg>
</div>

<div style="margin-top: 6rem;"></div>

## Deploy in Seconds

<div class="terminal-window">
  <div class="terminal-header">
    <div class="terminal-dot red"></div>
    <div class="terminal-dot yellow"></div>
    <div class="terminal-dot green"></div>
  </div>
  <div class="terminal-body">
    <div class="command-line">
      <span class="prompt">$</span>
      <span>agentform init my-agent</span>
    </div>
    <div style="color: #666; margin: 5px 0 15px 0;">Created my-agent.af in ./my-agent</div>
    
    <div class="command-line">
      <span class="prompt">$</span>
      <span>agentform deploy</span>
    </div>
    <div style="margin-top: 5px;">
      <div>> Validating schema... <span style="color: #27c93f">OK</span></div>
      <div>> Provisioning resources... <span style="color: #27c93f">Done</span></div>
      <div>> Syncing to edge... <span style="color: #27c93f">Success</span></div>
      <div style="margin-top: 10px; color: #27c93f;">➜ Agent live at https://api.agentform.com/v1/agents/my-agent</div>
    </div>
    
    <div class="command-line" style="margin-top: 15px;">
      <span class="prompt">$</span>
      <span class="cursor"></span>
    </div>
  </div>
</div>

<div style="margin-top: 6rem;"></div>

## Code that speaks your language

=== "Agentform DSL"

    ```terraform
    agent "researcher" {
      model = "gpt-4-turbo"
      temperature = 0.7
      
      system_prompt = "You are a senior research analyst."
      
      tools = [
        "web_search",
        "summarize_page"
      ]

      limits {
        budget = "5.00"
        max_steps = 10
      }
    }
    ```

=== "JSON Schema"

    ```json
    {
      "name": "researcher",
      "model": "gpt-4-turbo",
      "temperature": 0.7,
      "system_prompt": "You are a senior research analyst.",
      "tools": [
        "web_search", 
        "summarize_page"
      ],
      "limits": {
        "budget": "5.00",
        "max_steps": 10
      }
    }
    ```

=== "Python SDK (Coming Soon)"

    ```python
    # Planned Python SDK example.
    # The agentform Python package and Agent class are not yet available.
    # This example illustrates the intended future interface.
    #
    # from agentform import Agent
    #
    # researcher = Agent(
    #     name="researcher",
    #     model="gpt-4-turbo",
    #     temperature=0.7,
    #     system_prompt="You are a senior research analyst.",
    #     tools=["web_search", "summarize_page"],
    #     limits={
    #         "budget": "5.00",
    #         "max_steps": 10
    #     }
    # )
    ```

<div style="margin-top: 4rem;"></div>
