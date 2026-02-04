# Customer Support Agent with Escalation Logic

## Overview
Modern customer support systems must balance automation with human
intervention. While many user queries can be handled automatically,
some issues are ambiguous, sensitive, or too complex and must be
escalated to a human agent.

This example demonstrates how Agentform can be used to model a
clear, maintainable customer support workflow using a declarative,
agents-as-code approach.

---

## Problem
In traditional implementations, support logic is often scattered across
imperative scripts, conditional checks, and hard-coded fallbacks. This
makes systems difficult to reason about, modify, or extend.

Common challenges include:
- Determining when an automated agent should stop responding
- Handling unresolved or low-confidence cases
- Maintaining clarity as workflows grow in complexity

---

## Why Agentform
Agentform provides a structured and declarative way to define:
- Agents and their responsibilities
- Workflows that coordinate agent behavior
- Fallback paths for failure or uncertainty

By expressing support logic as configuration rather than ad hoc code,
Agentform makes workflows easier to understand, audit, and evolve over
time.

---

## Example Description
This example models a simple customer support system with escalation:

- A Customer Support Agent attempts to resolve incoming user queries
- If the agent cannot confidently resolve the issue, the request is
  escalated to a Human Escalation Agent
- The escalation logic is explicitly defined in the workflow rather
  than being buried in application code

---

## Workflow
1. A user submits a customer support request
2. The support agent attempts to resolve the issue
3. If resolution fails or confidence is insufficient, the workflow
   escalates the request to a human agent

This pattern mirrors real-world support systems used in production.

---

## Files
  - `customer-support.af` 

- Defines agents and the support workflow using the Agentform DSL

- This example uses the Agentform DSL (`.af`), which is the recommended
and current format for defining Agentform projects.



---

## How to Extend
This example can be extended in several ways:
- Add specialized agents (billing, technical support, onboarding)
- Introduce confidence thresholds or scoring logic
- Integrate external tools such as ticketing systems or knowledge bases
- Add retry or fallback strategies before escalation
