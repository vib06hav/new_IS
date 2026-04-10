"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

const ADMIN_SESSION_HISTORY_STORAGE_KEY = "admin-session-history-v1";
const MAX_ADMIN_SESSION_HISTORY_ENTRIES = 12;

export type AdminSessionHistoryTone =
  | "lime"
  | "blue"
  | "cyan"
  | "orange"
  | "pink"
  | "slate";

export type AdminSessionHistoryEntry = {
  id: string;
  action: string;
  reportId: string;
  detail: string;
  timestamp: number;
  tone: AdminSessionHistoryTone;
};

type AdminSessionHistoryContextValue = {
  entries: AdminSessionHistoryEntry[];
  addEntry: (entry: Omit<AdminSessionHistoryEntry, "id" | "timestamp">) => void;
  clearEntries: () => void;
};

const AdminSessionHistoryContext = createContext<AdminSessionHistoryContextValue | null>(null);

export function clearPersistedAdminSessionHistory() {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(ADMIN_SESSION_HISTORY_STORAGE_KEY);
}

export function AdminSessionHistoryProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [entries, setEntries] = useState<AdminSessionHistoryEntry[]>([]);
  const [hasHydrated, setHasHydrated] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const storedEntries = window.sessionStorage.getItem(ADMIN_SESSION_HISTORY_STORAGE_KEY);
    if (!storedEntries) {
      setHasHydrated(true);
      return;
    }

    try {
      const parsedEntries = JSON.parse(storedEntries) as AdminSessionHistoryEntry[];
      if (Array.isArray(parsedEntries)) {
        setEntries(parsedEntries);
      }
    } catch {
      window.sessionStorage.removeItem(ADMIN_SESSION_HISTORY_STORAGE_KEY);
    } finally {
      setHasHydrated(true);
    }
  }, []);

  useEffect(() => {
    if (!hasHydrated || typeof window === "undefined") {
      return;
    }

    window.sessionStorage.setItem(ADMIN_SESSION_HISTORY_STORAGE_KEY, JSON.stringify(entries));
  }, [entries, hasHydrated]);

  const addEntry = useCallback(
    (entry: Omit<AdminSessionHistoryEntry, "id" | "timestamp">) => {
      setEntries((current) => [
        {
          ...entry,
          id:
            typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
              ? crypto.randomUUID()
              : `${Date.now()}-${Math.random().toString(16).slice(2)}`,
          timestamp: Date.now(),
        },
        ...current,
      ].slice(0, MAX_ADMIN_SESSION_HISTORY_ENTRIES));
    },
    [],
  );

  const clearEntries = useCallback(() => {
    setEntries([]);
    clearPersistedAdminSessionHistory();
  }, []);

  const value = useMemo(
    () => ({
      entries,
      addEntry,
      clearEntries,
    }),
    [addEntry, clearEntries, entries],
  );

  return <AdminSessionHistoryContext.Provider value={value}>{children}</AdminSessionHistoryContext.Provider>;
}

export function useAdminSessionHistory() {
  const context = useContext(AdminSessionHistoryContext);

  if (!context) {
    throw new Error("useAdminSessionHistory must be used within an AdminSessionHistoryProvider.");
  }

  return context;
}
