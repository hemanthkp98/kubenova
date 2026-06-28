/**
 * @file Left sidebar navigation — Chat / Resources / Logs / Audit sections.
 */

import { MessageSquare, LayoutGrid, ScrollText, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

export type SidebarView = "chat" | "resources" | "logs" | "audit";

interface SidebarProps {
  activeView: SidebarView;
  onViewChange: (view: SidebarView) => void;
  className?: string;
}

const NAV_ITEMS: { id: SidebarView; icon: React.ReactNode; label: string }[] = [
  { id: "chat", icon: <MessageSquare size={18} />, label: "Chat" },
  { id: "resources", icon: <LayoutGrid size={18} />, label: "Resources" },
  { id: "logs", icon: <ScrollText size={18} />, label: "Logs" },
  { id: "audit", icon: <FileText size={18} />, label: "Audit" },
];

export function Sidebar({ activeView, onViewChange, className }: SidebarProps) {
  return (
    <nav
      className={cn(
        "flex flex-col items-center py-4 gap-1 bg-kn-bg-surface border-r border-kn-border w-14",
        className
      )}
      aria-label="Main navigation"
    >
      {NAV_ITEMS.map((item) => (
        <button
          key={item.id}
          onClick={() => onViewChange(item.id)}
          title={item.label}
          aria-label={item.label}
          aria-current={activeView === item.id ? "page" : undefined}
          className={cn(
            "w-10 h-10 rounded-lg flex items-center justify-center transition-colors",
            activeView === item.id
              ? "bg-kn-accent/15 text-kn-accent"
              : "text-kn-text-muted hover:text-kn-text-primary hover:bg-kn-bg-elevated"
          )}
        >
          {item.icon}
        </button>
      ))}
    </nav>
  );
}
