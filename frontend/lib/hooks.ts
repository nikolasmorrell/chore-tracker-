"use client";
import useSWR from "swr";
import { swrFetcher, ApiError } from "./api";

export function useApi<T>(path: string | null) {
  return useSWR<T, ApiError>(path, swrFetcher as (k: string) => Promise<T>, {
    revalidateOnFocus: false,
  });
}

export function formatDate(s: string | null | undefined): string {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleString();
  } catch {
    return s;
  }
}

export function formatBytes(n: number | null | undefined): string {
  if (n == null) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}
