/**
 * @file Audit CSV export button — triggers a browser file download.
 */

import { Download } from "lucide-react";
import { auditApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface AuditExportButtonProps {
  clusterContext?: string;
  riskLevel?: string;
  className?: string;
}

export function AuditExportButton({ clusterContext, riskLevel, className }: AuditExportButtonProps) {
  const handleExport = () => {
    const params: Record<string, string> = {};
    if (clusterContext) params.cluster_context = clusterContext;
    if (riskLevel) params.risk_level = riskLevel;
    const url = auditApi.exportCsvUrl(params);
    // Trigger browser download by navigating to the URL.
    const link = document.createElement("a");
    link.href = url;
    link.download = "kubenova-audit.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <button
      onClick={handleExport}
      className={cn(
        "flex items-center gap-2 px-3 py-1.5 text-xs rounded-md",
        "bg-kn-bg-elevated border border-kn-border text-kn-text-muted",
        "hover:text-kn-text-primary hover:border-kn-accent/50 transition-colors",
        className
      )}
      aria-label="Export audit log as CSV"
    >
      <Download size={13} />
      Export CSV
    </button>
  );
}
