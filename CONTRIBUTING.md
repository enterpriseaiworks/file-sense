# Contributing

Thank you for helping improve FileSense. The project should remain understandable to people who are new to RAG as well as maintainable by experienced engineers.

## Current implementation boundary

Implementation Phases 0–2 are approved. Changes may improve architecture records, workspace tooling, typed configuration, service foundations, and the local Docker topology. Do not add persistence, ingestion, retrieval, or grounded-chat behavior until the project owner approves the corresponding phase.

## Development principles

- Explain why a change is needed and who benefits.
- Keep the Streamlit UI separate from FastAPI and RAG internals.
- Keep provider-specific behavior behind integration boundaries.
- Preserve stable public API contracts.
- Add type hints to all Python interfaces.
- Never make unit tests depend on network services.
- Include deterministic tests for every feature and bug fix.
- Keep secrets, document text, questions, and answers out of logs.
- Update user documentation whenever behavior or configuration changes.

## Change conventions

Use Conventional Commit titles with a clear scope, for example:

```text
docs(readme): clarify local and cloud data boundaries
feat(indexer): add incremental PDF synchronization
fix(gateway): preserve exact-model routing policy
```

Pull requests should describe the user problem, the chosen solution, compatibility or security considerations, and any user-visible documentation changes.

## Quality checks

Install the locked workspace with `make sync`. Run formatting with `make format`, or run linting, strict type checking, and offline unit tests together with `make check`. Integration, evaluation, and end-to-end commands will be added with the behavior they verify.
