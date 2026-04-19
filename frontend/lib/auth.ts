import type { LogoutResponse, SessionResponse } from "@/lib/types";
import { getCsrfToken } from "@/lib/csrf";

export async function getSession() {
  const response = await fetch("/api/auth/session", {
    credentials: "same-origin",
    cache: "no-store",
  });
  if (!response.ok) {
    return null;
  }
  return (await response.json()) as SessionResponse;
}

export async function signOut() {
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
