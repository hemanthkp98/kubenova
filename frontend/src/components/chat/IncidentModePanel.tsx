/**
 * @file Incident response mode panel.
 *
 * Displayed when incident_mode is active in the chat store. Shows a
 * step-by-step breakdown of findings from the incident_analyzer_node
 * and probable root causes identified by the AI.
 */

import { AlertTriangle, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface IncidentModePanelProps {
  findings: string[];
  onClose: () => void;
  className?: string;
}

export function IncidentModePanel({ findings, onClose, className }: IncidentModePanelProps) {
  return (
    <div
      className={cn(
        "bg-kn-danger/10 border border-kn-danger/30 rounded-lg p-4",
        className
      )}
      role="alert"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-kn-danger">
          <AlertTriangle size={16} />
          <span className="text-sm font-semibold">Incident Response Mode</span>
        </div>
        <button
          onClick={onClose}
          className="text-kn-text-muted hover:text-kn-text-primary"
          aria-label="Exit incident mode"
        >
          <X size={14} />
        </button>
      </div>

      {findings.length === 0 ? (
        <p className="text-xs text-kn-text-muted">Analysing cluster state…</p>
      ) : (
        <div className="space-y-2">
          <p className="text-xs font-medium text-kn-text-muted uppercase tracking-wider">
            Findings ({findings.length})
          </p>
          <ol className="space-y-1.5">
            {findings.map((finding, i) => (
              <li key={i} className="flex gap-2">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-kn-danger/20 text-kn-danger text-[10px] flex items-center justify-center font-bold">
                  {i + 1}
                </span>
                <span className="text-xs text-kn-text-primary leading-5">{finding}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
