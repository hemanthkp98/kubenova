/**
 * @file Zustand store for chat message history and streaming state.
 *
 * Manages the full conversation history, the current streaming content
 * being assembled from token chunks, and the incident mode flag.
 */

import { create } from "zustand";
import type { ChatMessage, CommandPreview } from "@/types/chat";
import { generateId } from "@/lib/utils";

interface ChatState {
  messages: ChatMessage[];
  streamingContent: string;
  commandPreview: CommandPreview | null;
  isStreaming: boolean;
  incidentMode: boolean;

  addMessage: (role: ChatMessage["role"], content: string, preview?: CommandPreview) => ChatMessage;
  appendToken: (token: string) => void;
  flushStreaming: () => void;
  setCommandPreview: (preview: CommandPreview | null) => void;
  setIsStreaming: (streaming: boolean) => void;
  setIncidentMode: (mode: boolean) => void;
  clearHistory: () => void;
}

export const useChatStore = create<ChatState>()((set, get) => ({
  messages: [],
  streamingContent: "",
  commandPreview: null,
  isStreaming: false,
  incidentMode: false,

  addMessage: (role, content, preview) => {
    const msg: ChatMessage = {
      id: generateId(),
      role,
      content,
      timestamp: new Date(),
      commandPreview: preview,
    };
    set((state) => ({ messages: [...state.messages, msg] }));
    return msg;
  },

  appendToken: (token) =>
    set((state) => ({ streamingContent: state.streamingContent + token })),

  flushStreaming: () => {
    const { streamingContent, addMessage } = get();
    if (streamingContent.trim()) {
      addMessage("assistant", streamingContent);
    }
    set({ streamingContent: "", isStreaming: false });
  },

  setCommandPreview: (preview) => set({ commandPreview: preview }),

  setIsStreaming: (streaming) => set({ isStreaming: streaming }),

  setIncidentMode: (mode) => set({ incidentMode: mode }),

  clearHistory: () =>
    set({
      messages: [],
      streamingContent: "",
      commandPreview: null,
      isStreaming: false,
    }),
}));
