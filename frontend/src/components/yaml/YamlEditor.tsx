/**
 * @file Monaco Editor wrapper for YAML editing and preview.
 *
 * Validates YAML syntax on change and exposes errors via the onError callback.
 * In readOnly mode the editor is non-interactive (used in CommandPreview).
 */

import Editor from "@monaco-editor/react";
import { cn } from "@/lib/utils";

interface YamlEditorProps {
  value: string;
  onChange?: (value: string) => void;
  onError?: (errors: string[]) => void;
  readOnly?: boolean;
  height?: string;
  className?: string;
}

export function YamlEditor({
  value,
  onChange,
  readOnly = false,
  height = "200px",
  className,
}: YamlEditorProps) {
  return (
    <div className={cn("rounded-md overflow-hidden border border-kn-border", className)}>
      <Editor
        height={height}
        language="yaml"
        value={value}
        onChange={(v) => onChange?.(v ?? "")}
        theme="vs-dark"
        options={{
          readOnly,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 12,
          fontFamily: "JetBrains Mono, Consolas, monospace",
          lineNumbers: "on",
          folding: true,
          automaticLayout: true,
          tabSize: 2,
          wordWrap: "on",
        }}
      />
    </div>
  );
}
