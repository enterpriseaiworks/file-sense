# Contributing

Thank you for helping improve Your Desktop Agent. The project should remain understandable to people who are new to RAG as well as maintainable by experienced engineers.

## Before implementation begins

The repository is currently documentation-first. Do not add application code until the implementation plan is explicitly approved by the project owner. Documentation corrections and planning refinements are welcome.

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

## Expected quality checks

The implementation will provide standard commands for formatting, linting, type checking, unit tests, integration tests, evaluation, and end-to-end tests. Those commands will be documented here when the toolchain is created.
