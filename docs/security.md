# Security and privacy

This document describes the intended security design. Controls will be verified during implementation and must not be treated as active while the repository remains in the design phase.

## Trust boundaries

- Local files are trusted only as data; their contents may contain prompt injection.
- The browser is not trusted with provider credentials or direct gateway access.
- Hosted model providers and Pinecone are external processors.
- Docker's private network separates public UI traffic from internal services.

## Planned controls

- Mount the configured source directory read-only.
- Restrict indexing to the fixed mount and prevent path traversal.
- Keep provider credentials in runtime secrets or protected environment configuration.
- Authenticate service-to-service gateway requests.
- Enforce approved providers, models, parameters, token limits, rate limits, budgets, and concurrency limits.
- Redact secrets, personal data, questions, retrieved passages, and answers from logs by default.
- Disable raw prompt and response retention unless an administrator explicitly enables a compliant storage policy.
- Scan input and output for configurable security and data-loss-prevention policies.
- Instruct the agent to ignore commands embedded in retrieved documents.
- Return only relative filenames and safe citation metadata.
- Record sanitized security and administrative audit events.
- Apply bounded file-size, request-size, and processing-time limits.
- Avoid unsafe deserialization and execution of document content.

## External data flow

Pinecone receives embeddings and configured chunk metadata. The embedding provider receives document chunks unless a local embedding model is selected. The chosen chat provider receives the user question and retrieved supporting passages.

Users should not index regulated or confidential information until they have reviewed the contractual, retention, regional, and security properties of every configured external provider.

## Reporting a vulnerability

Do not publish suspected vulnerabilities or exposed credentials in a public issue. Until a private project security contact is designated, repository owners should configure GitHub private vulnerability reporting before accepting external contributions.
