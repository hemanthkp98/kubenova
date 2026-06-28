/**
 * @file Top navigation bar — logo, cluster switcher, LLM config, namespace switcher.
 */

import { useState } from "react";
import { Settings2, Zap } from "lucide-react";
import { ClusterSwitcher } from "./ClusterSwitcher";
import { NamespaceSwitcher } from "./NamespaceSwitcher";
import { LLMConfigModal } from "./LLMConfigModal";
import { useLLMStore } from "@/store/llmStore";
import { cn } from "@/lib/utils";

interface NavbarProps {
  className?: string;
}

export function Navbar({ className }: NavbarProps) {
  const [showLLMConfig, setShowLLMConfig] = useState(false);
  const { isConfigured, provider } = useLLMStore();

  return (
    <>
      <header
        className={cn(
          "flex items-center justify-between h-12 px-4 bg-kn-bg-surface border-b border-kn-border",
          className
        )}
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-md bg-kn-accent/20 flex items-center justify-center">
            <span className="text-kn-accent text-sm font-bold">⎈</span>
          </div>
          <span className="text-sm font-semibold text-kn-text-primary tracking-wide">KubeNova</span>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <NamespaceSwitcher />
          <ClusterSwitcher />

          {/* LLM config button */}
          <button
            onClick={() => setShowLLMConfig(true)}
            title="Configure LLM provider"
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-colors",
              "bg-kn-bg-elevated border border-kn-border",
              isConfigured
                ? "text-kn-purple border-kn-purple/30"
                : "text-kn-text-muted hover:text-kn-text-primary"
            )}
          >
            {isConfigured ? <Zap size={12} className="text-kn-purple" /> : <Settings2 size={12} />}
            <span className="font-mono">{isConfigured ? provider : "LLM"}</span>
          </button>
        </div>
      </header>

      {showLLMConfig && <LLMConfigModal onClose={() => setShowLLMConfig(false)} />}
    </>
  );
}
