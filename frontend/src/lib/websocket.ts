/**
 * @file WebSocket factory with configurable base URL.
 *
 * Creates WebSocket instances pointing at the backend. In development the
 * Vite proxy rewrites /api/ws/* to ws://localhost:8000/api/ws/*.
 * In production the nginx reverse proxy handles the same rewrite.
 */

const WS_BASE = (() => {
  const envUrl = import.meta.env.VITE_WS_BASE_URL;
  if (envUrl) return envUrl;
  // Derive from current window location in browser environments.
  if (typeof window !== "undefined") {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${window.location.host}`;
  }
  return "ws://localhost:8000";
})();

/**
 * Create a WebSocket connection to a KubeNova backend path.
 *
 * @param path - Path relative to the backend root, e.g. "/api/ws/chat".
 * @returns A native WebSocket instance.
 */
export function createWebSocket(path: string): WebSocket {
  const url = `${WS_BASE}${path}`;
  return new WebSocket(url);
}

/**
 * Build the log streaming WebSocket URL for a given pod container.
 *
 * @param namespace - Kubernetes namespace.
 * @param pod - Pod name.
 * @param container - Container name (use "_" for default container).
 * @param clusterContext - kubeconfig context name.
 * @param tail - Number of historical lines to include.
 */
export function logStreamUrl(
  namespace: string,
  pod: string,
  container: string,
  clusterContext: string,
  tail = 100
): string {
  const enc = encodeURIComponent;
  return `${WS_BASE}/api/ws/logs/${enc(namespace)}/${enc(pod)}/${enc(container)}?cluster_context=${enc(clusterContext)}&tail=${tail}`;
}
