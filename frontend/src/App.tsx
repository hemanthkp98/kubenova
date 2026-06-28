/**
 * @file Root application component.
 *
 * Provides the top-level layout: Navbar across the top, Sidebar on the left,
 * and a main content area that switches between Chat, Resources, Logs, and Audit views.
 *
 * No external router is used — the app is a single-page tool where navigation
 * is handled by local state, keeping the bundle lean.
 */

import { useState } from "react";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar, type SidebarView } from "@/components/layout/Sidebar";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { ResourcePanel } from "@/components/resources/ResourcePanel";
import { AuditTable } from "@/components/audit/AuditTable";
import { AuditExportButton } from "@/components/audit/AuditExportButton";
import { useChatStore } from "@/store/chatStore";
import { generateId } from "@/lib/utils";
import { useClusterStore } from "@/store/clusterStore";

const SESSION_ID = generateId();

export default function App() {
  const [view, setView] = useState<SidebarView>("chat");
  const { addMessage } = useChatStore();
  const { activeCluster } = useClusterStore();

  const handleAskAI = (message: string) => {
    setView("chat");
    // Pre-fill the chat by adding the message as a user message.
    addMessage("user", message);
  };

  return (
    <div className="flex flex-col h-screen bg-kn-bg-base overflow-hidden">
      <Navbar />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar activeView={view} onViewChange={setView} />

        {/* Main content */}
        <main className="flex-1 overflow-hidden">
          {view === "chat" && (
            <div className="flex h-full">
              {/* Chat takes ~65%, resource panel takes ~35% */}
              <ChatPanel sessionId={SESSION_ID} className="flex-[65]" />
              <ResourcePanel
                onAskAI={handleAskAI}
                className="flex-[35] min-w-[280px] max-w-[420px]"
              />
            </div>
          )}

          {view === "resources" && (
            <div className="h-full overflow-y-auto">
              <ResourcePanel onAskAI={handleAskAI} className="h-full" />
            </div>
          )}

          {view === "logs" && (
            <div className="h-full flex items-center justify-center text-kn-text-muted">
              <p className="text-sm">Select a pod from the Pods tab to view its logs.</p>
            </div>
          )}

          {view === "audit" && (
            <div className="h-full overflow-y-auto p-6">
              <div className="flex items-center justify-between mb-4">
                <h1 className="text-base font-semibold text-kn-text-primary">Audit Log</h1>
                <AuditExportButton clusterContext={activeCluster} />
              </div>
              <AuditTable />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
