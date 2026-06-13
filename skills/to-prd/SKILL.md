---
name: to-prd
description: "Turn current context into a PRD and publish it to the project issue tracker."
---

# To PRD

Source: https://github.com/mattpocock/skills/blob/main/skills/engineering/to-prd/SKILL.md

Turn the current conversation context and codebase understanding into a PRD. Do not interview the user from scratch; synthesize what is already known. Ask only for missing tracker/label details or a decision that materially changes scope.

Loop mode: in `bram-maintainer-loop`, draft the PRD to clarify broad work before implementation. Publish to GitHub only when issue creation is authorized.

## Process

1. Explore the repo enough to understand current state. Use project glossary terms. Respect relevant ADRs/docs.

2. Sketch major modules to build or modify. Look for deep modules that encapsulate meaningful behavior behind small, testable interfaces.

A deep module, as opposed to a shallow module, encapsulates substantial functionality in a simple interface that rarely changes.

3. Check with the user that the module split matches expectations, and ask which modules they want tested.

4. Write the PRD using the template below.

5. Publish to the project issue tracker. Prefer `gh issue create` in GitHub repos. Apply `ready-for-agent` if it exists or can be created by repo norms; otherwise use the closest repo-local triage label and mention the fallback.

## PRD Template

```markdown
## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A long, numbered list of user stories. Each user story should use:

1. As an <actor>, I want a <feature>, so that <benefit>

Cover all meaningful aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- modules that will be built or modified
- interfaces that will be modified
- technical clarifications from the developer
- architectural decisions
- schema changes
- API contracts
- specific interactions

Do not include specific file paths or code snippets. They may become stale quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can, such as a state machine, reducer, schema, or type shape, inline only the decision-rich part and note that it came from a prototype.

## Testing Decisions

A list of testing decisions that were made. Include:

- what makes a good test: external behavior, not implementation details
- which modules will be tested
- prior art for similar tests in the codebase

## Out of Scope

Things out of scope for this PRD.

## Further Notes

Any further notes about the feature.
```
