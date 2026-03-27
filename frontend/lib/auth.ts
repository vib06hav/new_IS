import type { SessionResponse } from "@/lib/types";
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
  await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "same-origin",
    headers,
  });
}
