# Architect runner prompt

Use this prompt for each independent candidate in Phase B. Pass the task and Phase A grounding artifacts. The runner is read-only and returns one candidate design package; it does not edit the repository.

Read the **architect** skill in full first. Output a candidate design package: type sketch, function signatures, module map, and prose rationale shaped per [`rationale-template.md`](rationale-template.md).

Apply this discipline:

- Caller's usage first. Write README-style usage and two or three real call sites before the types, then derive the type sketch from them.
- Data structures first. Trace each dominant access pattern through the proposed structure.
- Interface depth. Prefer a simple interface that pulls complexity into the callee. Parse transport or wire types into domain types behind the interface.
- Shared state. If two actors might both write, ask what happens. Prefer per-actor state with a merge at the read boundary when sharing is not a real invariant.
- Make boundaries visible. Use `not implemented` bodies, pseudocode for tricky logic, and concise intent/invariant comments.
- Encode invariants in types where practical. Prefer hard-to-misuse types over runtime checks or prose.
- Validate at boundaries and trust types inside. Keep business logic pure and the shell thin.
- Keep a single source of truth per invariant. Derive instead of synchronizing.
- Prefer idempotent state transitions. Ask what happens if an operation runs twice or crashes halfway.
- Keep call chains short. If tracing the flow needs more than three files, consider flattening the hierarchy.

Produce one strong, structurally distinct candidate. Do not hedge toward a safe-looking middle; differences between candidates are the exploration signal.
