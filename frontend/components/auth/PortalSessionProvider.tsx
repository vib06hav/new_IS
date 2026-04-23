"use client";

import { createContext, useContext, useEffect, useRef, useSyncExternalStore } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader } from "@/components/ui/Loader";
import {
  type PortalSessionSnapshot,
  clearWorkflowActive,
  getSessionSnapshot,
  markWorkflowActive,
  revalidateSession,
  subscribeToSessionStore,
} from "@/lib/auth";
import type { UserRole } from "@/lib/types";

const KEEPALIVE_INTERVAL_MS = 5 * 60 * 1000;
const EMPTY_SERVER_SNAPSHOT: PortalSessionSnapshot = {
  authState: "loading",
  session: null,
  lastKnownGoodSession: null,
  lastValidationTime: null,
  forbiddenReason: null,
  workflowCount: 0,
};

type PortalSessionContextValue = PortalSessionSnapshot & {
  portal: UserRole;
  revalidate: (options?: { force?: boolean; reason?: string }) => Promise<PortalSessionSnapshot>;
  markWorkflowActive: () => void;
  clearWorkflowActive: () => void;
};

const PortalSessionContext = createContext<PortalSessionContextValue | null>(null);

export function PortalSessionProvider({
  children,
  loginHref,
  portal,
}: {
  children: React.ReactNode;
  loginHref: string;
  portal: UserRole;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const snapshot = useSyncExternalStore(subscribeToSessionStore, getSessionSnapshot, () => EMPTY_SERVER_SNAPSHOT);
  const redirectHandledRef = useRef<string | null>(null);
  const isPublicPortalRoute = pathname === loginHref;

  useEffect(() => {
    if (isPublicPortalRoute) {
      return;
    }
    void revalidateSession({ portal, reason: "portal-bootstrap" });
  }, [isPublicPortalRoute, portal]);

  useEffect(() => {
    if (isPublicPortalRoute) {
      return;
    }

    function handleFocus() {
      void revalidateSession({ portal, reason: "window-focus" });
    }

    function handleVisibilityChange() {
      if (document.visibilityState === "visible") {
        void revalidateSession({ portal, reason: "visibility-visible" });
      }
    }

    function handleOnline() {
      void revalidateSession({ portal, reason: "network-online" });
    }

    window.addEventListener("focus", handleFocus);
    window.addEventListener("online", handleOnline);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.removeEventListener("focus", handleFocus);
      window.removeEventListener("online", handleOnline);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [isPublicPortalRoute, portal]);

  useEffect(() => {
    if (isPublicPortalRoute) {
      return;
    }

    const intervalId = window.setInterval(() => {
      if (document.visibilityState !== "visible" || navigator.onLine === false) {
        return;
      }

      void revalidateSession({ portal, reason: "keepalive" });
    }, KEEPALIVE_INTERVAL_MS);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [isPublicPortalRoute, portal]);

  useEffect(() => {
    if (isPublicPortalRoute) {
      redirectHandledRef.current = null;
      return;
    }

    const isDeactivated = snapshot.forbiddenReason?.toLowerCase().includes("deactivated") ?? false;
    const redirectKey = `${snapshot.authState}:${snapshot.forbiddenReason ?? ""}`;

    if (snapshot.authState === "expired") {
      if (redirectHandledRef.current !== redirectKey) {
        redirectHandledRef.current = redirectKey;
        console.warn("[auth] forced login redirect", { portal, state: snapshot.authState });
        router.replace(loginHref);
      }
      return;
    }

    if (snapshot.authState === "forbidden" && !isDeactivated) {
      if (redirectHandledRef.current !== redirectKey) {
        redirectHandledRef.current = redirectKey;
        console.warn("[auth] forced login redirect", {
          portal,
          state: snapshot.authState,
          reason: snapshot.forbiddenReason,
        });
        router.replace(loginHref);
      }
      return;
    }

    redirectHandledRef.current = null;
  }, [isPublicPortalRoute, loginHref, portal, router, snapshot.authState, snapshot.forbiddenReason]);

  const contextValue: PortalSessionContextValue = {
    ...snapshot,
    portal,
    revalidate: (options) => revalidateSession({ ...options, portal }),
    markWorkflowActive,
    clearWorkflowActive,
  };

  const isDeactivated = snapshot.forbiddenReason?.toLowerCase().includes("deactivated") ?? false;
  const isBlockingLoading =
    snapshot.authState === "loading" || (snapshot.authState === "refreshing" && !snapshot.session);
  const isRedirectingAway = snapshot.authState === "expired" || (snapshot.authState === "forbidden" && !isDeactivated);

  if (isPublicPortalRoute) {
    return <PortalSessionContext.Provider value={contextValue}>{children}</PortalSessionContext.Provider>;
  }

  if (isBlockingLoading) {
    return <Loader label="Checking session..." fullscreen />;
  }

  if (isRedirectingAway) {
    return <Loader label="Redirecting to sign in..." fullscreen />;
  }

  if (snapshot.authState === "forbidden" && isDeactivated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-6 py-10">
        <div className="w-full max-w-xl rounded-[1.6rem] border border-amber-200 bg-white p-8 shadow-[0_18px_44px_rgba(15,23,42,0.08)]">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-amber-700">Access blocked</p>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">This account is deactivated.</h1>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            Your session was recognized, but this account no longer has portal access. Please contact an administrator
            if this looks incorrect.
          </p>
        </div>
      </div>
    );
  }

  if (snapshot.authState === "unavailable" && !snapshot.session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-6 py-10">
        <div className="w-full max-w-xl rounded-[1.6rem] border border-slate-200 bg-white p-8 shadow-[0_18px_44px_rgba(15,23,42,0.08)]">
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500">Session unavailable</p>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900">We could not verify your session.</h1>
          <p className="mt-3 text-sm leading-7 text-slate-600">
            The authentication service looks temporarily unavailable. Please try again in a moment.
          </p>
        </div>
      </div>
    );
  }

  return <PortalSessionContext.Provider value={contextValue}>{children}</PortalSessionContext.Provider>;
}

export function usePortalSession() {
  const context = useContext(PortalSessionContext);
  if (!context) {
    throw new Error("usePortalSession must be used within PortalSessionProvider");
  }
  return context;
}
