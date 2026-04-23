import type { LogoutResponse, SessionResponse, UserRole } from "@/lib/types";
import { getCsrfToken } from "@/lib/csrf";

export type PortalAuthState = "loading" | "authenticated" | "refreshing" | "expired" | "forbidden" | "unavailable";

export type PortalSessionSnapshot = {
  authState: PortalAuthState;
  session: SessionResponse | null;
  lastKnownGoodSession: SessionResponse | null;
  lastValidationTime: number | null;
  forbiddenReason: string | null;
  workflowCount: number;
};

type ValidationOptions = {
  force?: boolean;
  portal?: UserRole;
  reason?: string;
};

type SessionState = PortalSessionSnapshot;

type SessionStore = SessionState & {
  inflightValidation: Promise<PortalSessionSnapshot> | null;
};

const listeners = new Set<() => void>();

const initialSessionState: SessionState = {
  authState: "loading",
  session: null,
  lastKnownGoodSession: null,
  lastValidationTime: null,
  forbiddenReason: null,
  workflowCount: 0,
};

const sessionStore: SessionStore = {
  ...initialSessionState,
  inflightValidation: null,
};

let currentSnapshot: PortalSessionSnapshot = initialSessionState;

function emitSessionStore() {
  listeners.forEach((listener) => listener());
}

function updateSessionStore(next: Partial<SessionStore>) {
  Object.assign(sessionStore, next);
  currentSnapshot = {
    authState: sessionStore.authState,
    session: sessionStore.session,
    lastKnownGoodSession: sessionStore.lastKnownGoodSession,
    lastValidationTime: sessionStore.lastValidationTime,
    forbiddenReason: sessionStore.forbiddenReason,
    workflowCount: sessionStore.workflowCount,
  };
  emitSessionStore();
}

function buildSessionUrl(portal?: UserRole) {
  if (!portal) {
    return "/api/auth/session";
  }

  return `/api/auth/session?portal=${encodeURIComponent(portal)}`;
}

async function parseSessionError(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (typeof payload.detail === "string" && payload.detail.trim()) {
      return payload.detail;
    }
  } catch {
    // Fall back to response metadata below.
  }

  return response.statusText || `Session validation failed with ${response.status}`;
}

export function getSessionSnapshot(): PortalSessionSnapshot {
  return currentSnapshot;
}

export function subscribeToSessionStore(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function clearSessionCache() {
  updateSessionStore({
    authState: "loading",
    session: null,
    lastKnownGoodSession: null,
    lastValidationTime: null,
    forbiddenReason: null,
    workflowCount: 0,
    inflightValidation: null,
  });
}

export async function revalidateSession(options?: ValidationOptions) {
  const force = options?.force ?? false;
  if (!force && sessionStore.inflightValidation) {
    return sessionStore.inflightValidation;
  }

  const currentSession = sessionStore.lastKnownGoodSession ?? sessionStore.session;
  updateSessionStore({
    authState: currentSession ? "refreshing" : "loading",
    forbiddenReason: null,
  });

  sessionStore.inflightValidation = (async () => {
    try {
      const response = await fetch(buildSessionUrl(options?.portal), {
        credentials: "same-origin",
        cache: "no-store",
      });

      if (response.status === 200) {
        const session = (await response.json()) as SessionResponse;
        const snapshot: PortalSessionSnapshot = {
          authState: "authenticated",
          session,
          lastKnownGoodSession: session,
          lastValidationTime: Date.now(),
          forbiddenReason: null,
          workflowCount: sessionStore.workflowCount,
        };
        updateSessionStore(snapshot);
        console.info("[auth] session validation success", {
          portal: options?.portal ?? null,
          reason: options?.reason ?? null,
        });
        return snapshot;
      }

      const detail = await parseSessionError(response);
      if (response.status === 401) {
        const snapshot: PortalSessionSnapshot = {
          authState: "expired",
          session: null,
          lastKnownGoodSession: null,
          lastValidationTime: Date.now(),
          forbiddenReason: null,
          workflowCount: sessionStore.workflowCount,
        };
        updateSessionStore(snapshot);
        console.warn("[auth] session expired", {
          portal: options?.portal ?? null,
          reason: options?.reason ?? null,
        });
        return snapshot;
      }

      if (response.status === 403) {
        const snapshot: PortalSessionSnapshot = {
          authState: "forbidden",
          session: null,
          lastKnownGoodSession: null,
          lastValidationTime: Date.now(),
          forbiddenReason: detail,
          workflowCount: sessionStore.workflowCount,
        };
        updateSessionStore(snapshot);
        console.warn("[auth] session forbidden", {
          portal: options?.portal ?? null,
          reason: options?.reason ?? null,
          detail,
        });
        return snapshot;
      }

      const snapshot: PortalSessionSnapshot = {
        authState: "unavailable",
        session: currentSession,
        lastKnownGoodSession: currentSession,
        lastValidationTime: Date.now(),
        forbiddenReason: null,
        workflowCount: sessionStore.workflowCount,
      };
      updateSessionStore(snapshot);
      console.error("[auth] session validation unavailable", {
        portal: options?.portal ?? null,
        reason: options?.reason ?? null,
        status: response.status,
        detail,
      });
      return snapshot;
    } catch (error) {
      const snapshot: PortalSessionSnapshot = {
        authState: "unavailable",
        session: currentSession,
        lastKnownGoodSession: currentSession,
        lastValidationTime: Date.now(),
        forbiddenReason: null,
        workflowCount: sessionStore.workflowCount,
      };
      updateSessionStore(snapshot);
      console.error("[auth] session validation transport failure", {
        portal: options?.portal ?? null,
        reason: options?.reason ?? null,
        error: error instanceof Error ? error.message : "Unknown transport error",
      });
      return snapshot;
    } finally {
      sessionStore.inflightValidation = null;
    }
  })();

  return sessionStore.inflightValidation;
}

export async function getSession(options?: ValidationOptions) {
  const snapshot = await revalidateSession(options);
  return snapshot.session;
}

export function markWorkflowActive() {
  updateSessionStore({
    workflowCount: sessionStore.workflowCount + 1,
  });
}

export function clearWorkflowActive() {
  updateSessionStore({
    workflowCount: Math.max(0, sessionStore.workflowCount - 1),
  });
}

export async function signOut() {
  clearSessionCache();
  const headers = new Headers();
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers.set("X-CSRF-Token", csrfToken);
  }
  const response = await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "same-origin",
    headers,
  });
  let payload: LogoutResponse | null = null;
  try {
    payload = (await response.json()) as LogoutResponse;
  } catch {
    payload = null;
  }
  if (payload?.logout_url) {
    window.location.assign(payload.logout_url);
    return;
  }
  window.location.assign("/");
}
