/// <reference types="vite/client" />

/**
 * @file Vite environment type declarations.
 * Exposes typed `import.meta.env` variables used throughout the frontend.
 */

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_WS_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
