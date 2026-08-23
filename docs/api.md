# API Reference

REST and WebSocket endpoint specifications, request payloads, and response schemas for KubeNova.

---

## Chat

### POST /api/chat

Single-turn chat request. Runs the full agent synchronously and returns when done.

**Request body**

```json
{
  "message": "show me all pods in the default namespace",
  "cluster_context": "minikube",
  "namespace": "default",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| message | string | yes | Natural language user message |
| cluster_context | string | yes | kubeconfig context name |
| namespace | string | no | Kubernetes namespace (default: "default") |
| session_id | string | yes | Client-generated UUID for correlation |

**Response 200**

```json
{
  "response": "Found 3 pods in the default namespace: nginx-abc, redis-xyz, postgres-def.",
  "command_preview": null,
  "audit_event_id": "7b3c1e2f-4a5b-6c7d-8e9f-0a1b2c3d4e5f"
}
```

**Errors**: 422 Unprocessable Entity (validation), 500 Internal Server Error.

---

### POST /api/chat/approve

Approve or reject a pending command after reviewing the dry-run preview.

**Request body**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "audit_event_id": "7b3c1e2f-4a5b-6c7d-8e9f-0a1b2c3d4e5f",
  "approved": true
}
```

**Response 200**

```json
{ "status": "accepted" }
```

---

### GET /api/chat/llm-info

Return the active LLM provider and model name as configured on the backend.

**Response 200**
```json
{
  "provider": "openai",
  "model": "gemini-2.5-flash"
}
```

`provider` is one of `anthropic`, `openai`, or `ollama`. When using Google Gemini, `provider` is `openai` (Gemini uses the OpenAI-compatible endpoint).

---

### WS /api/ws/chat

Streaming chat WebSocket. All messages are JSON-encoded strings.

Conversation history (messages, cluster context, namespace) is maintained server-side for the lifetime of the WebSocket connection. Each message inherits the context set by previous messages in the same session. Sending `cluster_context` or `namespace` on any message updates the session-level value for all subsequent messages.

#### Client → Server messages

**Chat message:**
```json
{
  "type": "chat",
  "message": "restart the api-server deployment",
  "cluster_context": "production",
  "namespace": "default",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Approval message:**
```json
{
  "type": "approval",
  "approved": true,
  "audit_event_id": "7b3c1e2f-4a5b-6c7d-8e9f-0a1b2c3d4e5f",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Clear context message** (resets server-side conversation history and cluster context for this session):
```json
{ "type": "clear_context" }
```
Server response: `{"type": "done", "content": "context_cleared"}`

#### Server → Client messages

**Token chunk** (stream AI response text incrementally):
```json
{ "type": "token", "content": "I found the following " }
```

**Command preview** (pause for user approval):
```json
{
  "type": "command_preview",
  "content": {
    "kubectl_command": "kubectl rollout restart deployment/api-server -n default",
    "manifest_yaml": null,
    "diff": "+ deployment.apps/api-server restarted",
    "warnings": ["Rolling restart will cause a brief interruption."],
    "resource_name": "api-server",
    "resource_kind": "Deployment",
    "risk_level": "HIGH",
    "is_safe": true
  }
}
```

**Done:**
```json
{ "type": "done", "content": "" }
```

**Error:**
```json
{ "type": "error", "content": "Connection to cluster timed out." }
```

---

## Clusters

### GET /api/clusters

List all kubeconfig contexts.

**Response 200**
```json
[
  {
    "name": "minikube",
    "cluster": "minikube",
    "user": "minikube",
    "namespace": "default",
    "is_active": true
  }
]
```

### GET /api/clusters/{name}/status

Health check for a specific cluster.

**Response 200**
```json
{
  "context_name": "minikube",
  "server": "https://192.168.49.2:8443",
  "reachable": true,
  "node_count": 1,
  "pod_count": 12,
  "version": "v1.30.0"
}
```

### POST /api/clusters/switch

Switch the active cluster context.

**Request body**
```json
{ "context_name": "production" }
```

**Response 200**: ClusterContext object.
**Response 404**: Context not found in kubeconfig.

---

## Resources

All resource endpoints accept:
- `cluster_context` (required): kubeconfig context name
- `namespace` (optional): Kubernetes namespace, default "default", use "all" for all namespaces

### GET /api/resources/pods

**Example**
```bash
curl "http://localhost:8000/api/resources/pods?cluster_context=minikube&namespace=default"
```

**Response** — array of PodInfo objects:
```json
[
  {
    "name": "nginx-abc123",
    "namespace": "default",
    "status": "Running",
    "ready": "1/1",
    "restarts": 0,
    "age": "2h",
    "node": "minikube",
    "labels": {"app": "nginx"},
    "containers": [...]
  }
]
```

### GET /api/resources/deployments
### GET /api/resources/services
### GET /api/resources/nodes
### GET /api/resources/namespaces
### GET /api/resources/events

Similar patterns — see `app/models/resource.py` for the full field list.

---

## Logs

### WS /api/ws/logs/{namespace}/{pod}/{container}

Stream pod logs line by line.

**Query parameters**:
- `cluster_context`: kubeconfig context name
- `tail`: Number of historical lines to include (default: 100)

**Messages**: Plain text strings, one log line per message.

---

## Audit Log

### GET /api/audit

Paginated audit events.

**Query parameters**:

| Parameter | Type | Description |
|---|---|---|
| page | integer | 1-based page number (default: 1) |
| page_size | integer | Items per page (default: 50, max: 500) |
| cluster_context | string | Filter by cluster |
| risk_level | string | Filter by risk: LOW, MEDIUM, HIGH, CRITICAL |
| from_date | datetime | ISO-8601 start date filter |
| to_date | datetime | ISO-8601 end date filter |

**Response 200**
```json
{
  "items": [...],
  "total": 142,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

### GET /api/audit/export

Export matching audit events as CSV.

Accepts the same filter parameters as GET /api/audit.

**Response**: `text/csv` with `Content-Disposition: attachment; filename="kubenova-audit.csv"`.

**CSV columns**: `id, timestamp, session_id, user_intent, cluster_context, namespace, generated_command, risk_level, approved, error`
