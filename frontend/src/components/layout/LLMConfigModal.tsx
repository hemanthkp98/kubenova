/**
 * @file LLM configuration modal.
 *
 * Lets the user select a provider (Anthropic, OpenAI, Ollama) and supply
 * an API key or base URL. Keys are stored in sessionStorage only and are
 * cleared when the tab closes.
 *
 * A prominent security notice is shown to ensure the operator understands
 * the key is ephemeral.
 */

import { useState } from "react";
import { X, AlertCircle } from "lucide-react";
import { useLLMStore, type LLMProvider } from "@/store/llmStore";
import { cn } from "@/lib/utils";

interface LLMConfigModalProps {
  onClose: () => void;
}

const PROVIDERS: { id: LLMProvider; label: string }[] = [
  { id: "anthropic", label: "Anthropic (Claude)" },
  { id: "openai", label: "OpenAI (GPT)" },
  { id: "ollama", label: "Ollama (Local)" },
];

export function LLMConfigModal({ onClose }: LLMConfigModalProps) {
  const { provider, model, apiKey, baseUrl, setProvider, setModel, setApiKey, setBaseUrl, clearConfig } = useLLMStore();
  const [localKey, setLocalKey] = useState(apiKey);
  const [localUrl, setLocalUrl] = useState(baseUrl);
  const [localModel, setLocalModel] = useState(model);

  const handleSave = () => {
    setApiKey(localKey);
    setBaseUrl(localUrl);
    setModel(localModel);
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="LLM configuration"
    >
      <div className="w-full max-w-md mx-4 bg-kn-bg-surface border border-kn-border rounded-xl shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-kn-border">
          <h2 className="text-sm font-semibold text-kn-text-primary">LLM Provider Configuration</h2>
          <button onClick={onClose} className="text-kn-text-muted hover:text-kn-text-primary">
            <X size={18} />
          </button>
        </div>

        {/* Security notice */}
        <div className="mx-4 mt-4 p-3 rounded-md bg-kn-warning/10 border border-kn-warning/30 flex gap-2">
          <AlertCircle size={14} className="text-kn-warning flex-shrink-0 mt-0.5" />
          <p className="text-xs text-kn-text-primary">
            Your API key is stored <strong>only for this browser session</strong> and is cleared when you close the tab.
          </p>
        </div>

        {/* Form */}
        <div className="p-4 space-y-4">
          {/* Provider selector */}
          <div>
            <label className="block text-xs text-kn-text-muted mb-1.5">Provider</label>
            <div className="flex gap-2">
              {PROVIDERS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setProvider(p.id)}
                  className={cn(
                    "flex-1 px-2 py-2 rounded-md border text-xs transition-colors",
                    provider === p.id
                      ? "border-kn-accent text-kn-accent bg-kn-accent/10"
                      : "border-kn-border text-kn-text-muted hover:border-kn-accent/50"
                  )}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Model */}
          <div>
            <label className="block text-xs text-kn-text-muted mb-1.5">Model</label>
            <input
              type="text"
              value={localModel}
              onChange={(e) => setLocalModel(e.target.value)}
              className={cn(
                "w-full px-3 py-2 rounded-md text-xs font-mono",
                "bg-kn-bg-base border border-kn-border text-kn-text-primary",
                "focus:outline-none focus:ring-1 focus:ring-kn-accent"
              )}
            />
          </div>

          {/* API Key (Anthropic / OpenAI) */}
          {provider !== "ollama" && (
            <div>
              <label className="block text-xs text-kn-text-muted mb-1.5">API Key</label>
              <input
                type="password"
                value={localKey}
                onChange={(e) => setLocalKey(e.target.value)}
                placeholder="sk-…"
                className={cn(
                  "w-full px-3 py-2 rounded-md text-xs font-mono",
                  "bg-kn-bg-base border border-kn-border text-kn-text-primary",
                  "focus:outline-none focus:ring-1 focus:ring-kn-accent"
                )}
              />
            </div>
          )}

          {/* Base URL (Ollama) */}
          {provider === "ollama" && (
            <div>
              <label className="block text-xs text-kn-text-muted mb-1.5">Ollama Base URL</label>
              <input
                type="text"
                value={localUrl}
                onChange={(e) => setLocalUrl(e.target.value)}
                placeholder="http://localhost:11434"
                className={cn(
                  "w-full px-3 py-2 rounded-md text-xs font-mono",
                  "bg-kn-bg-base border border-kn-border text-kn-text-primary",
                  "focus:outline-none focus:ring-1 focus:ring-kn-accent"
                )}
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-kn-border">
          <button
            onClick={() => { clearConfig(); onClose(); }}
            className="text-xs text-kn-text-muted hover:text-kn-danger transition-colors"
          >
            Clear & Reset
          </button>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-4 py-2 text-xs text-kn-text-muted hover:text-kn-text-primary">
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 text-xs font-medium rounded-md bg-kn-accent text-white hover:bg-kn-accent/90"
            >
              Save
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
