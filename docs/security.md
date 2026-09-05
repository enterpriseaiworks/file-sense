# Security and privacy

This document distinguishes implemented controls from controls that still require production policy and integration work.

## Trust boundaries

- Local files are trusted only as data; their contents may contain prompt injection.
- The browser is not trusted with provider credentials or direct gateway access.
- Hosted model providers and Pinecone are external processors.
- Docker's private network separates public UI traffic from internal services.

## Implemented controls

- Mount the configured source directory read-only and reject symlinks, oversized files, and paths outside the mount.
- Keep provider credentials in backend runtime configuration and route model traffic through LiteLLM.
- Require an application API key for model, conversation, and chat endpoints using constant-time comparison.
- Restrict selectable chat models to configured aliases.
- Treat retrieved passages and conversation transcripts as untrusted data in gateway prompts.
- Apply bounded request/file sizes and bounded ingestion retries.
- Store audit metadata without questions, retrieved passages, or generated answers.
- Return relative filenames and citation coordinates instead of absolute host paths.
- Keep filenames hidden in normal chat. Explicit file requests may display the exact filename while
  using opaque file IDs and five-minute HMAC-signed download links. Reject traversal and symlinks,
  enforce type/size limits, and audit successful downloads without recording paths or tokens.

## Remaining controls

- Enforce approved providers, models, parameters, token limits, rate limits, budgets, and concurrency limits.
- Redact secrets, personal data, questions, retrieved passages, and answers from logs by default.
- Disable raw prompt and response retention unless an administrator explicitly enables a compliant storage policy.
- Scan input and output for configurable security and data-loss-prevention policies.
- Avoid unsafe deserialization and execution of document content.

## External data flow

Pinecone receives embeddings and configured chunk metadata. The embedding provider receives document chunks unless a local embedding model is selected. The chosen chat provider receives the user question and retrieved supporting passages.

Users should not index regulated or confidential information until they have reviewed the contractual, retention, regional, and security properties of every configured external provider.

## Reporting a vulnerability

Do not publish suspected vulnerabilities or exposed credentials in a public issue. Until a private project security contact is designated, repository owners should configure GitHub private vulnerability reporting before accepting external contributions.
