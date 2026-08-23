# Security

This document describes KubeNova's security model, known limitations, and responsible disclosure process.

---

## API key storage

- API keys entered in the **LLM Config modal** are stored in `sessionStorage` only. They are automatically cleared when the browser tab is closed. They are never sent to the backend in any form other than the LLM API call.
- API keys set via **environment variables** (`LLM_API_KEY`) are read by the backend process on startup. They are never written to the audit log, never included in HTTP response bodies, and are redacted from all log output.
- The audit log schema deliberately excludes the API key. Even if the SQLite file were extracted, it would contain no credentials.

---

## The dry-run safety gate

Before any `kubectl apply` or destructive operation reaches the cluster, KubeNova:

1. Runs `kubectl apply --dry-run=server` on the generated manifest.
2. Presents the diff, warnings, and risk classification to the operator in the **CommandPreview modal**.
3. Requires an explicit button click to proceed (Enter key does not approve — intentional safety UX).

CRITICAL-risk operations (namespace delete, node drain, `--all` deletes) are blocked by the agent before reaching the dry-run stage. They cannot be approved via the UI.

---

## RBAC requirements

KubeNova needs cluster access to read resources and (optionally) apply changes. The Helm chart creates a service account with a ClusterRole. For production deployments, review the ClusterRole in `helm/kubenova/templates/clusterrole.yaml` and restrict the write verbs to specific namespaces using RoleBindings if full cluster-wide write is not appropriate.

The minimal read-only configuration (sufficient for querying and diagnostics) requires no write permissions at all.

---

## Audit log integrity

The SQLite audit log records every user interaction with:
- Timestamp, session ID, cluster context
- Raw user intent (the natural language message)
- Generated kubectl command (if any)
- Risk level, dry-run result, approval decision
- Execution result and error (if any)

The log is append-only by convention (no rows are updated after the interaction completes, except to fill in the approval decision). It is not cryptographically signed in the MVP — consider adding a write-once append log or an external SIEM integration for high-compliance environments.

---

## Network security

- The backend **never forwards cluster credentials** to the frontend. The kubeconfig file is mounted into the backend container only.
- All cluster API calls are made server-side by the Python `kubernetes` SDK using the mounted kubeconfig.
- The frontend communicates only with the KubeNova backend — it has no direct access to cluster APIs.

---

## Known limitations (MVP)

- The SQLite audit log has no access controls — any user who can read the container filesystem can read it. Use a PostgreSQL backend with proper access controls for production.
- There is no authentication layer on the KubeNova API itself in the MVP. Deploy behind an authenticating reverse proxy (OAuth2, SSO) for production use.
- The session ID is client-generated and not cryptographically authenticated.

---

## Responsible disclosure

To report a security vulnerability, please email **security@kubenova.dev** with:

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact assessment
4. (Optional) Suggested fix

We will respond within 48 hours and aim to release a patch within 7 days for critical issues. Public disclosure is coordinated with the reporter.

Please do not open a public GitHub issue for security vulnerabilities.
