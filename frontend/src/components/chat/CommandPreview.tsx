/**
 * @file Command preview modal — the safety gate in the UI.
 *
 * Shown when the agent generates a command that requires confirmation.
 * The user must explicitly click "Apply to Cluster" — Enter does not approve
 * (safety UX: prevent accidental approval by keyboard users).
 *
 * Features:
 * - Risk badge coloured by level
 * - kubectl command with copy button
 * - Unified diff rendering (green additions, red removals)
 * - Warnings list
 * - Read-only Monaco YAML editor
 * - Escape closes / cancels
 */

import { useEffect, useRef } from "react";
import { X, Copy, Check, AlertTriangle, ShieldAlert, Shield, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CommandPreview as CommandPreviewType, RiskLevel } from "@/types/chat";
import { YamlEditor } from "@/components/yaml/YamlEditor";
import { useState } from "react";

interface CommandPreviewProps {
  preview: CommandPreviewType;
  auditEventId: string;
  onApprove: (auditEventId: string, manifestYaml?: string) => void;
  onCancel: (auditEventId: string) => void;
}

const RISK_CONFIG: Record<RiskLevel, { label: string; color: string; icon: React.ReactNode }> = {
  LOW: { label: "LOW RISK", color: "text-kn-success border-kn-success bg-kn-success/10", icon: <ShieldCheck size={14} /> },
  MEDIUM: { label: "MEDIUM RISK", color: "text-kn-warning border-kn-warning bg-kn-warning/10", icon: <Shield size={14} /> },
  HIGH: { label: "HIGH RISK", color: "text-orange-400 border-orange-400 bg-orange-400/10", icon: <AlertTriangle size={14} /> },
  CRITICAL: { label: "CRITICAL", color: "text-kn-danger border-kn-danger bg-kn-danger/10", icon: <ShieldAlert size={14} /> },
};

function DiffLine({ line }: { line: string }) {
  if (line.startsWith("+")) {
    return <div className="text-kn-success bg-kn-success/5 px-2 font-mono text-xs">{line}</div>;
  }
  if (line.startsWith("-")) {
    return <div className="text-kn-danger bg-kn-danger/5 px-2 font-mono text-xs">{line}</div>;
  }
  return <div className="text-kn-text-muted px-2 font-mono text-xs">{line}</div>;
}

export function CommandPreview({ preview, auditEventId, onApprove, onCancel }: CommandPreviewProps) {
  const [copied, setCopied] = useState(false);
  const [editedYaml, setEditedYaml] = useState(preview.manifest_yaml || "");
  const approveButtonRef = useRef<HTMLButtonElement>(null);
  const risk = RISK_CONFIG[preview.risk_level];
  const isCritical = preview.risk_level === "CRITICAL";

  // Escape key cancels.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel(auditEventId);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [auditEventId, onCancel]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(preview.kubectl_command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Command preview"
    >
      <div className="w-full max-w-2xl mx-4 bg-kn-bg-surface border border-kn-border rounded-xl shadow-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-kn-border">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold text-kn-text-primary">Command Preview</h2>
            <span
              className={cn(
                "flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium",
                risk.color
              )}
            >
              {risk.icon}
              {risk.label}
            </span>
          </div>
          <button
            onClick={() => onCancel(auditEventId)}
            className="text-kn-text-muted hover:text-kn-text-primary transition-colors"
            aria-label="Cancel"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* kubectl command */}
          <div>
            <p className="text-xs text-kn-text-muted uppercase tracking-wider mb-2">Generated Command</p>
            <div className="flex items-center gap-2 bg-kn-bg-base rounded-md p-3 border border-kn-border">
              <code className="flex-1 text-kn-accent font-mono text-xs break-all">
                {preview.kubectl_command}
              </code>
              <button
                onClick={handleCopy}
                className="flex-shrink-0 text-kn-text-muted hover:text-kn-text-primary"
                aria-label="Copy command"
              >
                {copied ? <Check size={14} className="text-kn-success" /> : <Copy size={14} />}
              </button>
            </div>
          </div>

          {/* Warnings */}
          {preview.warnings.length > 0 && (
            <div className="rounded-md bg-kn-warning/10 border border-kn-warning/30 p-3">
              <p className="text-xs font-medium text-kn-warning mb-1">Warnings</p>
              <ul className="space-y-1">
                {preview.warnings.map((w, i) => (
                  <li key={i} className="text-xs text-kn-text-primary font-mono">{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Dry-run diff */}
          {preview.diff && (
            <div>
              <p className="text-xs text-kn-text-muted uppercase tracking-wider mb-2">Dry-run Diff</p>
              <div className="bg-kn-bg-base rounded-md border border-kn-border overflow-auto max-h-48">
                {preview.diff.split("\n").map((line, i) => (
                  <DiffLine key={i} line={line} />
                ))}
              </div>
            </div>
          )}

          {/* YAML editor (editable) */}
          {preview.manifest_yaml && (
            <div>
              <p className="text-xs text-kn-text-muted uppercase tracking-wider mb-2">Manifest YAML (Editable)</p>
              <YamlEditor value={editedYaml} onChange={setEditedYaml} />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-kn-border">
          <button
            onClick={() => onCancel(auditEventId)}
            className="px-4 py-2 text-sm text-kn-text-muted hover:text-kn-text-primary transition-colors"
            data-testid="cancel-button"
          >
            Cancel
          </button>
          <button
            ref={approveButtonRef}
            onClick={() => onApprove(auditEventId, preview.manifest_yaml ? editedYaml : undefined)}
            disabled={isCritical || !preview.is_safe}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-md transition-colors",
              isCritical || !preview.is_safe
                ? "bg-kn-border text-kn-text-muted cursor-not-allowed"
                : "bg-kn-accent text-white hover:bg-kn-accent/90"
            )}
            data-testid="approve-button"
          >
            Apply to Cluster
          </button>
        </div>
      </div>
    </div>
  );
}
