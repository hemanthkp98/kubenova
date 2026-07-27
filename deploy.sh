#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                   KubeNova — Kubernetes Deployer                       ║
# ║                                                                        ║
# ║  Usage:  ./deploy.sh [--config <path>] [--dry-run]                     ║
# ║                                                                        ║
# ║  Reads kubenova.conf, builds Docker images, and deploys KubeNova       ║
# ║  to your Kubernetes cluster — no Helm required.                        ║
# ╚══════════════════════════════════════════════════════════════════════════╝
set -euo pipefail

# ── Terminal colors ─────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()    { echo -e "${CYAN}→${NC} $*"; }
ok()     { echo -e "${GREEN}✓${NC} $*"; }
warn()   { echo -e "${YELLOW}⚠${NC}  $*"; }
header() { echo -e "\n${BOLD}$*${NC}"; }
die()    { echo -e "\n${RED}✗  ERROR:${NC} $*\n" >&2; exit 1; }
step()   { echo -e "\n${BOLD}${CYAN}[$1/8]${NC} $2"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=false

# ── Parse arguments ──────────────────────────────────────────────────────────
CONFIG_FILE="${SCRIPT_DIR}/kubenova.conf"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --config) CONFIG_FILE="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        -h|--help)
            echo "Usage: ./deploy.sh [--config <path>] [--dry-run]"
            echo "  --config <path>   Path to config file (default: ./kubenova.conf)"
            echo "  --dry-run         Validate config and print manifests without applying"
            exit 0 ;;
        *) die "Unknown argument: $1. Run ./deploy.sh --help for usage." ;;
    esac
done

# ════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║      KubeNova Kubernetes Deployer        ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
if $DRY_RUN; then warn "DRY-RUN mode — manifests will be printed, not applied"; fi

# ════════════════════════════════════════════════════════════════════════════
step 1 "Loading configuration"
# ════════════════════════════════════════════════════════════════════════════

[[ -f "$CONFIG_FILE" ]] || die "Config file not found: $CONFIG_FILE\n\n  Make a copy of the example and edit it:\n    cp kubenova.conf.example kubenova.conf\n  Then re-run: ./deploy.sh"

# shellcheck source=kubenova.conf
source "$CONFIG_FILE"

# ── Apply defaults for optional fields ───────────────────────────────────────
NAMESPACE="${NAMESPACE:-kubenova}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
BACKEND_REPLICAS="${BACKEND_REPLICAS:-1}"
FRONTEND_REPLICAS="${FRONTEND_REPLICAS:-1}"
EXPOSE_TYPE="${EXPOSE_TYPE:-LoadBalancer}"
DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./kubenova.db}"
KUBENOVA_ENV="${KUBENOVA_ENV:-production}"
LLM_PROVIDER="${LLM_PROVIDER:-anthropic}"
LLM_MODEL="${LLM_MODEL:-claude-3-5-haiku-20241022}"
LLM_API_KEY="${LLM_API_KEY:-}"
LLM_BASE_URL="${LLM_BASE_URL:-}"
NODEPORT="${NODEPORT:-30080}"
CORS_ORIGINS="${CORS_ORIGINS:-[\"*\"]}"
KUBE_CONTEXT="${KUBE_CONTEXT:-}"
REGISTRY="${REGISTRY:-}"

# ── Validate required fields ─────────────────────────────────────────────────
[[ -n "${KUBECONFIG_PATH:-}" ]] || die "KUBECONFIG_PATH is not set in $CONFIG_FILE"

# Expand ~ in path
KUBECONFIG_PATH="${KUBECONFIG_PATH/#\~/$HOME}"
[[ -f "$KUBECONFIG_PATH" ]] || die "Kubeconfig file not found: $KUBECONFIG_PATH\n  Verify KUBECONFIG_PATH in $CONFIG_FILE"

if [[ "$LLM_PROVIDER" != "ollama" && -z "$LLM_API_KEY" ]]; then
    die "LLM_API_KEY is required when LLM_PROVIDER=${LLM_PROVIDER}\n  Set it in $CONFIG_FILE, Section 3."
fi

if [[ "$EXPOSE_TYPE" != "LoadBalancer" && "$EXPOSE_TYPE" != "NodePort" ]]; then
    die "EXPOSE_TYPE must be 'LoadBalancer' or 'NodePort' (got: ${EXPOSE_TYPE})"
fi

ok "Config loaded from $CONFIG_FILE"
echo "   Namespace   : ${NAMESPACE}"
echo "   LLM Provider: ${LLM_PROVIDER} / ${LLM_MODEL}"
echo "   Expose Type : ${EXPOSE_TYPE}"
echo "   Registry    : ${REGISTRY:-<local cluster>}"

# ════════════════════════════════════════════════════════════════════════════
step 2 "Checking prerequisites"
# ════════════════════════════════════════════════════════════════════════════

command -v docker &>/dev/null  || die "'docker' is not installed or not in PATH.\n  Install: https://docs.docker.com/get-docker/"
command -v kubectl &>/dev/null || die "'kubectl' is not installed or not in PATH.\n  Install: https://kubernetes.io/docs/tasks/tools/"
docker info &>/dev/null        || die "Docker daemon is not running. Start Docker Desktop and try again."
ok "docker and kubectl are available"

# ════════════════════════════════════════════════════════════════════════════
step 3 "Verifying cluster connectivity"
# ════════════════════════════════════════════════════════════════════════════

# Build base kubectl command with kubeconfig
KUBECTL="kubectl --kubeconfig=${KUBECONFIG_PATH}"
[[ -n "$KUBE_CONTEXT" ]] && KUBECTL="${KUBECTL} --context=${KUBE_CONTEXT}"

$KUBECTL cluster-info &>/dev/null || die \
    "Cannot connect to cluster.\n\n  Check:\n  • KUBECONFIG_PATH = ${KUBECONFIG_PATH}\n  • KUBE_CONTEXT    = ${KUBE_CONTEXT:-<current-context>}\n  • The cluster API server is reachable from this machine"

CURRENT_CONTEXT=$($KUBECTL config current-context 2>/dev/null || echo "unknown")
CLUSTER_SERVER=$($KUBECTL config view --minify -o jsonpath='{.clusters[0].cluster.server}' 2>/dev/null || echo "unknown")
ok "Connected to cluster"
echo "   Context     : ${CURRENT_CONTEXT}"
echo "   API Server  : ${CLUSTER_SERVER}"

# ── Detect local cluster type ─────────────────────────────────────────────────
CLUSTER_TYPE="remote"
if echo "$CURRENT_CONTEXT" | grep -qE "^kind-";     then CLUSTER_TYPE="kind";      fi
if echo "$CURRENT_CONTEXT" | grep -qE "^k3d-";      then CLUSTER_TYPE="k3d";       fi
if echo "$CURRENT_CONTEXT" | grep -qE "^minikube";  then CLUSTER_TYPE="minikube";  fi

if [[ -z "$REGISTRY" && "$CLUSTER_TYPE" == "remote" ]]; then
    die "REGISTRY must be set for remote clusters.\n\n  In $CONFIG_FILE, Section 2, set:\n    REGISTRY=\"ghcr.io/yourorg\"  (or your ECR/GCR/ACR URL)\n\n  Leave REGISTRY empty only for local clusters (kind / k3d / minikube)."
fi

if [[ -n "$REGISTRY" ]]; then
    BACKEND_IMAGE="${REGISTRY}/kubenova-backend:${IMAGE_TAG}"
    FRONTEND_IMAGE="${REGISTRY}/kubenova-frontend:${IMAGE_TAG}"
    PULL_POLICY="Always"
else
    BACKEND_IMAGE="kubenova-backend:${IMAGE_TAG}"
    FRONTEND_IMAGE="kubenova-frontend:${IMAGE_TAG}"
    PULL_POLICY="Never"
    warn "Local mode: images will be loaded directly into ${CLUSTER_TYPE} (no registry push)"
fi

# ════════════════════════════════════════════════════════════════════════════
step 4 "Building Docker images"
# ════════════════════════════════════════════════════════════════════════════

if $DRY_RUN; then
    warn "Dry-run: skipping image build"
else
    log "Building backend image: ${BACKEND_IMAGE} ..."
    docker build --quiet -t "${BACKEND_IMAGE}" "${SCRIPT_DIR}/backend" \
        || die "Backend Docker build failed.\n  Run manually to debug: docker build -t ${BACKEND_IMAGE} ./backend"
    ok "Backend image built: ${BACKEND_IMAGE}"

    log "Building frontend image: ${FRONTEND_IMAGE} ..."
    docker build --quiet -t "${FRONTEND_IMAGE}" "${SCRIPT_DIR}/frontend" \
        || die "Frontend Docker build failed.\n  Run manually to debug: docker build -t ${FRONTEND_IMAGE} ./frontend"
    ok "Frontend image built: ${FRONTEND_IMAGE}"
fi

# ════════════════════════════════════════════════════════════════════════════
step 5 "Delivering images to cluster"
# ════════════════════════════════════════════════════════════════════════════

if $DRY_RUN; then
    warn "Dry-run: skipping image delivery"
elif [[ -n "$REGISTRY" ]]; then
    log "Pushing images to registry: ${REGISTRY} ..."
    docker push "${BACKEND_IMAGE}"  || die "Failed to push backend image: ${BACKEND_IMAGE}\n  Ensure you are logged in to your registry: docker login ${REGISTRY%%/*}"
    docker push "${FRONTEND_IMAGE}" || die "Failed to push frontend image: ${FRONTEND_IMAGE}"
    ok "Images pushed to ${REGISTRY}"
else
    # Derive cluster name from context (strip kind-/k3d- prefix)
    CLUSTER_NAME=$(echo "$CURRENT_CONTEXT" | sed 's/^kind-//' | sed 's/^k3d-//')
    log "Loading images into ${CLUSTER_TYPE} cluster '${CLUSTER_NAME}' ..."

    case "$CLUSTER_TYPE" in
        kind)
            command -v kind &>/dev/null || die \
                "'kind' CLI not found. Install: https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
            kind load docker-image "${BACKEND_IMAGE}" "${FRONTEND_IMAGE}" --name "${CLUSTER_NAME}" \
                || die "kind image load failed"
            ;;
        k3d)
            command -v k3d &>/dev/null || die \
                "'k3d' CLI not found. Install: https://k3d.io"
            k3d image import "${BACKEND_IMAGE}" "${FRONTEND_IMAGE}" -c "${CLUSTER_NAME}" \
                || die "k3d image import failed"
            ;;
        minikube)
            command -v minikube &>/dev/null || die \
                "'minikube' CLI not found. Install: https://minikube.sigs.k8s.io/docs/start/"
            minikube image load "${BACKEND_IMAGE}" \
                || die "minikube image load (backend) failed"
            minikube image load "${FRONTEND_IMAGE}" \
                || die "minikube image load (frontend) failed"
            ;;
    esac
    ok "Images loaded into ${CLUSTER_TYPE} cluster"
fi

# ════════════════════════════════════════════════════════════════════════════
step 6 "Applying Kubernetes manifests"
# ════════════════════════════════════════════════════════════════════════════

# Encode API key for Secret
LLM_API_KEY_B64=$(echo -n "${LLM_API_KEY}" | base64 | tr -d '\n')
LLM_BASE_URL_SAFE="${LLM_BASE_URL:-}"

# Service port config
if [[ "$EXPOSE_TYPE" == "NodePort" ]]; then
    SERVICE_TYPE="NodePort"
    NODEPORT_LINE="      nodePort: ${NODEPORT}"
else
    SERVICE_TYPE="LoadBalancer"
    NODEPORT_LINE=""
fi

# Build the full manifest as a single document
MANIFESTS=$(cat <<YAML
# ── Namespace ──────────────────────────────────────────────────────────────
apiVersion: v1
kind: Namespace
metadata:
  name: ${NAMESPACE}
  labels:
    app.kubernetes.io/managed-by: kubenova-deploy
---
# ── ServiceAccount ─────────────────────────────────────────────────────────
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kubenova
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/name: kubenova
automountServiceAccountToken: true
---
# ── ClusterRole ────────────────────────────────────────────────────────────
# Grants KubeNova read access for cluster inspection + write access for
# applying changes. All write commands require explicit user approval in the UI.
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kubenova
  labels:
    app.kubernetes.io/name: kubenova
rules:
  # Core workload resources — read
  - apiGroups: [""]
    resources:
      - pods
      - pods/log
      - pods/exec
      - services
      - nodes
      - namespaces
      - events
      - configmaps
      - persistentvolumes
      - persistentvolumeclaims
      - resourcequotas
      - limitranges
      - endpoints
      - serviceaccounts
      - secrets
    verbs: [get, list, watch]
  # Apps workloads — read
  - apiGroups: [apps]
    resources:
      - deployments
      - statefulsets
      - daemonsets
      - replicasets
    verbs: [get, list, watch]
  # Batch workloads — read
  - apiGroups: [batch]
    resources: [jobs, cronjobs]
    verbs: [get, list, watch]
  # Networking — read
  - apiGroups: [networking.k8s.io]
    resources: [ingresses, networkpolicies]
    verbs: [get, list, watch]
  # Storage — read
  - apiGroups: [storage.k8s.io]
    resources: [storageclasses]
    verbs: [get, list, watch]
  # RBAC — read (for cluster inspection)
  - apiGroups: [rbac.authorization.k8s.io]
    resources: [roles, rolebindings, clusterroles, clusterrolebindings]
    verbs: [get, list, watch]
  # HPA & VPA — read
  - apiGroups: [autoscaling]
    resources: [horizontalpodautoscalers]
    verbs: [get, list, watch]
  # Custom Resource Definitions — read
  - apiGroups: [apiextensions.k8s.io]
    resources: [customresourcedefinitions]
    verbs: [get, list, watch]
  # Write access — all resources/groups.
  # Every mutating command generated by the AI goes through a safety gate
  # and requires explicit Approve click in the KubeNova UI before execution.
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: [create, update, patch, delete, deletecollection]
---
# ── ClusterRoleBinding ─────────────────────────────────────────────────────
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kubenova
  labels:
    app.kubernetes.io/name: kubenova
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kubenova
subjects:
  - kind: ServiceAccount
    name: kubenova
    namespace: ${NAMESPACE}
---
# ── ConfigMap ──────────────────────────────────────────────────────────────
apiVersion: v1
kind: ConfigMap
metadata:
  name: kubenova-config
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/name: kubenova
data:
  KUBENOVA_ENV: "${KUBENOVA_ENV}"
  KUBENOVA_LOG_LEVEL: "INFO"
  KUBENOVA_DATABASE_URL: "${DATABASE_URL}"
  KUBENOVA_CORS_ORIGINS: '${CORS_ORIGINS}'
  LLM_PROVIDER: "${LLM_PROVIDER}"
  LLM_MODEL: "${LLM_MODEL}"
  LLM_BASE_URL: "${LLM_BASE_URL_SAFE}"
  MAX_LOG_LINES: "500"
  AUDIT_PAGE_SIZE: "50"
---
# ── Secret ─────────────────────────────────────────────────────────────────
apiVersion: v1
kind: Secret
metadata:
  name: kubenova-secret
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/name: kubenova
type: Opaque
data:
  LLM_API_KEY: ${LLM_API_KEY_B64}
---
# ── Backend Deployment ─────────────────────────────────────────────────────
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubenova-backend
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/name: kubenova
    app.kubernetes.io/component: backend
spec:
  replicas: ${BACKEND_REPLICAS}
  selector:
    matchLabels:
      app: kubenova-backend
  template:
    metadata:
      labels:
        app: kubenova-backend
        app.kubernetes.io/component: backend
    spec:
      serviceAccountName: kubenova
      automountServiceAccountToken: true
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
      containers:
        - name: backend
          image: ${BACKEND_IMAGE}
          imagePullPolicy: ${PULL_POLICY}
          ports:
            - name: http
              containerPort: 8000
              protocol: TCP
          envFrom:
            - configMapRef:
                name: kubenova-config
          env:
            - name: LLM_API_KEY
              valueFrom:
                secretKeyRef:
                  name: kubenova-secret
                  key: LLM_API_KEY
          livenessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 15
            periodSeconds: 30
            failureThreshold: 3
            timeoutSeconds: 5
          readinessProbe:
            httpGet:
              path: /healthz
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3
            timeoutSeconds: 5
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: 1000m
              memory: 512Mi
---
# ── Backend Service (named "backend" — nginx.conf proxy resolves this) ─────
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/name: kubenova
    app.kubernetes.io/component: backend
spec:
  type: ClusterIP
  ports:
    - port: 8000
      targetPort: http
      protocol: TCP
      name: http
  selector:
    app: kubenova-backend
---
# ── Frontend Deployment ────────────────────────────────────────────────────
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kubenova-frontend
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/name: kubenova
    app.kubernetes.io/component: frontend
spec:
  replicas: ${FRONTEND_REPLICAS}
  selector:
    matchLabels:
      app: kubenova-frontend
  template:
    metadata:
      labels:
        app: kubenova-frontend
        app.kubernetes.io/component: frontend
    spec:
      containers:
        - name: frontend
          image: ${FRONTEND_IMAGE}
          imagePullPolicy: ${PULL_POLICY}
          ports:
            - name: http
              containerPort: 80
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 10
            periodSeconds: 30
            timeoutSeconds: 5
          readinessProbe:
            httpGet:
              path: /
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 5
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 128Mi
---
# ── Frontend Service (external access point) ───────────────────────────────
apiVersion: v1
kind: Service
metadata:
  name: kubenova
  namespace: ${NAMESPACE}
  labels:
    app.kubernetes.io/name: kubenova
    app.kubernetes.io/component: frontend
spec:
  type: ${SERVICE_TYPE}
  ports:
    - port: 80
      targetPort: http
      protocol: TCP
      name: http
${NODEPORT_LINE}
  selector:
    app: kubenova-frontend
YAML
)

if $DRY_RUN; then
    warn "Dry-run: printing manifests (not applying)"
    echo ""
    echo "────────── MANIFESTS ──────────"
    echo "$MANIFESTS"
    echo "───────────────────────────────"
    echo ""
    ok "Dry-run complete. Remove --dry-run to apply."
    exit 0
fi

echo "$MANIFESTS" | $KUBECTL apply -f - \
    || die "kubectl apply failed.\n  Check the error above for details."

ok "All Kubernetes resources applied successfully"

# ════════════════════════════════════════════════════════════════════════════
step 7 "Waiting for rollout"
# ════════════════════════════════════════════════════════════════════════════

log "Waiting for backend pods to be ready (timeout: 120s) ..."
$KUBECTL rollout status deployment/kubenova-backend \
    -n "${NAMESPACE}" --timeout=120s \
    || warn "Backend rollout timed out. Check logs:\n  kubectl logs -n ${NAMESPACE} -l app=kubenova-backend --tail=50"

log "Waiting for frontend pods to be ready (timeout: 60s) ..."
$KUBECTL rollout status deployment/kubenova-frontend \
    -n "${NAMESPACE}" --timeout=60s \
    || warn "Frontend rollout timed out. Check logs:\n  kubectl logs -n ${NAMESPACE} -l app=kubenova-frontend --tail=50"

# ════════════════════════════════════════════════════════════════════════════
step 8 "Getting access URL"
# ════════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     KubeNova deployed successfully! 🚀  ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""

ACCESS_URL=""

if [[ "$EXPOSE_TYPE" == "NodePort" ]]; then
    # Get the first node's external IP, fall back to internal IP
    NODE_IP=$($KUBECTL get nodes \
        -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}' 2>/dev/null || true)
    if [[ -z "$NODE_IP" ]]; then
        NODE_IP=$($KUBECTL get nodes \
            -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || true)
    fi
    NODE_IP="${NODE_IP:-<node-ip>}"
    ACCESS_URL="http://${NODE_IP}:${NODEPORT}"
    echo -e "  ${CYAN}Access URL:${NC}   ${BOLD}${ACCESS_URL}${NC}"
else
    # LoadBalancer — wait up to 90 seconds for external IP assignment
    log "Waiting for LoadBalancer IP (up to 90s) ..."
    EXTERNAL_IP=""
    for i in $(seq 1 30); do
        EXTERNAL_IP=$($KUBECTL get svc kubenova -n "${NAMESPACE}" \
            -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || true)
        # Some clouds use hostname instead of IP (e.g. AWS ELB)
        if [[ -z "$EXTERNAL_IP" ]]; then
            EXTERNAL_IP=$($KUBECTL get svc kubenova -n "${NAMESPACE}" \
                -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)
        fi
        [[ -n "$EXTERNAL_IP" ]] && break
        sleep 3
    done

    if [[ -n "$EXTERNAL_IP" ]]; then
        ACCESS_URL="http://${EXTERNAL_IP}"
        echo -e "  ${CYAN}Access URL:${NC}   ${BOLD}${ACCESS_URL}${NC}"
    else
        warn "LoadBalancer IP not yet assigned (this is normal — cloud provisioning takes 1–3 min)."
        echo ""
        echo -e "  Watch for IP:   ${BOLD}kubectl get svc kubenova -n ${NAMESPACE} -w${NC}"
        echo ""
        echo -e "  Or use port-forward right now:"
        echo -e "  ${BOLD}kubectl port-forward svc/kubenova 8080:80 -n ${NAMESPACE}${NC}"
        echo -e "  Then open:      ${BOLD}http://localhost:8080${NC}"
    fi
fi

echo ""
echo -e "  ${CYAN}Namespace:${NC}    ${NAMESPACE}"
echo -e "  ${CYAN}API Docs:${NC}     ${ACCESS_URL:-http://<url>}/api/docs"
echo ""
echo -e "  Quick checks:"
echo -e "    ${BOLD}kubectl get pods -n ${NAMESPACE}${NC}"
echo -e "    ${BOLD}kubectl logs -n ${NAMESPACE} -l app=kubenova-backend --tail=30${NC}"
echo ""
echo -e "  To remove KubeNova from the cluster:"
echo -e "    ${BOLD}./teardown.sh${NC}"
echo ""
echo -e "${BOLD}══════════════════════════════════════════${NC}"
