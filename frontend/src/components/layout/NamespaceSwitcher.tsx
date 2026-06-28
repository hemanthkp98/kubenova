/**
 * @file Namespace switcher dropdown — filters all resource panel views.
 */

import { useState, useRef, useEffect } from "react";
import { ChevronDown, Layers } from "lucide-react";
import { useNamespaces } from "@/hooks/useResources";
import { useClusterStore } from "@/store/clusterStore";
import { cn } from "@/lib/utils";

interface NamespaceSwitcherProps {
  className?: string;
}

export function NamespaceSwitcher({ className }: NamespaceSwitcherProps) {
  const { activeNamespace, setActiveNamespace } = useClusterStore();
  const { data: namespaces } = useNamespaces();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const options = ["all", ...(namespaces ?? ["default"])];

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-md text-xs",
          "bg-kn-bg-elevated border border-kn-border text-kn-text-primary",
          "hover:border-kn-accent/50 transition-colors"
        )}
      >
        <Layers size={12} className="text-kn-text-muted" />
        <span className="font-mono">{activeNamespace}</span>
        <ChevronDown size={12} className={cn("transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div className="absolute top-full left-0 mt-1 w-44 bg-kn-bg-elevated border border-kn-border rounded-md shadow-xl z-50 py-1 max-h-60 overflow-y-auto">
          {options.map((ns) => (
            <button
              key={ns}
              onClick={() => { setActiveNamespace(ns); setOpen(false); }}
              className={cn(
                "w-full text-left px-3 py-1.5 text-xs font-mono",
                "hover:bg-kn-bg-base transition-colors",
                ns === activeNamespace && "text-kn-accent"
              )}
            >
              {ns}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
