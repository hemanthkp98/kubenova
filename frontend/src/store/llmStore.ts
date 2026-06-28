/**
 * @file Zustand store for LLM provider configuration.
 *
 * SECURITY: The API key is stored in sessionStorage, NOT localStorage.
 * It is cleared when the browser tab is closed. The user sees a warning
 * in the LLMConfigModal about this behaviour.
 *
 * The API key is never sent to the audit log or persisted server-side.
 */

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type LLMProvider = "anthropic" | "openai" | "ollama";

interface LLMState {
  provider: LLMProvider;
  model: string;
  apiKey: string;
  baseUrl: string;
  isConfigured: boolean;

  setProvider: (provider: LLMProvider) => void;
  setModel: (model: string) => void;
  setApiKey: (key: string) => void;
  setBaseUrl: (url: string) => void;
  clearConfig: () => void;
}

const DEFAULT_MODELS: Record<LLMProvider, string> = {
  anthropic: "claude-sonnet-4-6",
  openai: "gpt-4o",
  ollama: "llama3",
};

export const useLLMStore = create<LLMState>()(
  persist(
    (set, get) => ({
      provider: "anthropic",
      model: DEFAULT_MODELS.anthropic,
      apiKey: "",
      baseUrl: "",
      isConfigured: false,

      setProvider: (provider) =>
        set({ provider, model: DEFAULT_MODELS[provider] }),

      setModel: (model) => set({ model }),

      setApiKey: (apiKey) => set({ apiKey, isConfigured: apiKey.length > 0 }),

      setBaseUrl: (baseUrl) =>
        set({ baseUrl, isConfigured: get().provider === "ollama" || get().apiKey.length > 0 }),

      clearConfig: () =>
        set({ apiKey: "", baseUrl: "", isConfigured: false }),
    }),
    {
      name: "kubenova-llm",
      // sessionStorage: cleared when the tab closes. API keys do NOT survive sessions.
      storage: createJSONStorage(() => sessionStorage),
    }
  )
);
