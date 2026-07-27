#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                   KubeNova — Teardown Script                           ║
# ║                                                                        ║
# ║  Removes all KubeNova resources from the cluster.                      ║
# ║  Usage:  ./teardown.sh [--config <path>]                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

ok()  { echo -e "${GREEN}✓${NC} $*"; }
warn(){ echo -e "${YELLOW}⚠${NC}  $*"; }
die() { echo -e "\n${RED}✗  ERROR:${NC} $*\n" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/kubenova.conf"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --config) CONFIG_FILE="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: ./teardown.sh [--config <path>]"
            exit 0 ;;
        *) die "Unknown argument: $1" ;;
    esac
done

echo ""
echo -e "${BOLD}KubeNova — Teardown${NC}"
echo "────────────────────────────────────────"

[[ -f "$CONFIG_FILE" ]] || die "Config file not found: $CONFIG_FILE"
source "$CONFIG_FILE"

NAMESPACE="${NAMESPACE:-kubenova}"
KUBECONFIG_PATH="${KUBECONFIG_PATH:-$HOME/.kube/config}"
KUBECONFIG_PATH="${KUBECONFIG_PATH/#\~/$HOME}"
KUBE_CONTEXT="${KUBE_CONTEXT:-}"

[[ -f "$KUBECONFIG_PATH" ]] || die "Kubeconfig not found: $KUBECONFIG_PATH"

KUBECTL="kubectl --kubeconfig=${KUBECONFIG_PATH}"
[[ -n "$KUBE_CONTEXT" ]] && KUBECTL="${KUBECTL} --context=${KUBE_CONTEXT}"

$KUBECTL cluster-info &>/dev/null || die "Cannot connect to cluster. Check KUBECONFIG_PATH."

echo ""
echo -e "${YELLOW}This will permanently delete:${NC}"
echo "  • Namespace '${NAMESPACE}' and all resources within it"
echo "  • ClusterRole 'kubenova'"
echo "  • ClusterRoleBinding 'kubenova'"
echo ""
read -r -p "  Are you sure? Type 'yes' to confirm: " CONFIRM

if [[ "$CONFIRM" != "yes" ]]; then
    echo "Aborted."
    exit 0
fi

echo ""

# Delete cluster-scoped resources first (not namespaced)
echo "Removing cluster-scoped RBAC resources ..."
$KUBECTL delete clusterrolebinding kubenova --ignore-not-found=true
$KUBECTL delete clusterrole        kubenova --ignore-not-found=true
ok "ClusterRole and ClusterRoleBinding removed"

# Delete the namespace (this removes all namespaced resources)
echo "Deleting namespace '${NAMESPACE}' ..."
$KUBECTL delete namespace "${NAMESPACE}" --ignore-not-found=true --wait=true
ok "Namespace '${NAMESPACE}' deleted"

echo ""
echo -e "${GREEN}✓  KubeNova has been removed from the cluster.${NC}"
echo ""
