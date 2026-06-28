/**
 * @file Shared utility functions used throughout the KubeNova frontend.
 *
 * - `cn()`: Tailwind class merge helper (clsx + tailwind-merge).
 * - `formatBytes()`: Human-readable byte sizes.
 * - `formatAge()`: Human-readable duration from a date string.
 * - `truncate()`: Truncate long strings with an ellipsis.
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind class names, resolving conflicts correctly. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format a byte count into a human-readable string.
 *
 * @example formatBytes(1536) → "1.5 KB"
 */
export function formatBytes(bytes: number, decimals = 1): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}

/**
 * Format a date string or Date as a human-readable age (e.g. "2d3h", "45m").
 *
 * @param dateStr ISO-8601 date string or Date instance.
 * @returns Age string, or "unknown" if input is null/undefined.
 */
export function formatAge(dateStr: string | Date | null | undefined): string {
  if (!dateStr) return "unknown";
  const date = typeof dateStr === "string" ? new Date(dateStr) : dateStr;
  const now = Date.now();
  const diffMs = now - date.getTime();
  if (diffMs < 0) return "just now";
  const totalSeconds = Math.floor(diffMs / 1000);
  if (totalSeconds < 60) return `${totalSeconds}s`;
  if (totalSeconds < 3600) return `${Math.floor(totalSeconds / 60)}m`;
  if (totalSeconds < 86400) return `${Math.floor(totalSeconds / 3600)}h`;
  return `${Math.floor(totalSeconds / 86400)}d`;
}

/**
 * Truncate a string to a maximum length, appending "…" if needed.
 *
 * @param str Input string.
 * @param maxLength Maximum character count before truncation.
 * @returns The (possibly truncated) string.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - 1) + "…";
}

/**
 * Generate a random UUID-like string for session IDs.
 * Not cryptographically secure — used only for correlation, not auth.
 */
export function generateId(): string {
  return crypto.randomUUID
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2) + Date.now().toString(36);
}
