import type { UserRole } from "@/lib/types";

const TOKEN_KEY = "agis_access_token";

type DecodedToken = {
  sub: string;
  role: UserRole;
  exp?: number;
};

function decodeBase64Url(value: string) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  if (typeof window === "undefined") {
    return "";
  }
  return decodeURIComponent(
    window
      .atob(normalized)
      .split("")
      .map((character) => `%${(`00${character.charCodeAt(0).toString(16)}`).slice(-2)}`)
      .join(""),
  );
}

export function decodeToken(token: string): DecodedToken {
  const [, payload] = token.split(".");
  if (!payload) {
    throw new Error("Malformed token.");
  }
  return JSON.parse(decodeBase64Url(payload)) as DecodedToken;
}

export function saveToken(token: string) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(TOKEN_KEY, token);
  }
}

export function getToken() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(TOKEN_KEY);
  }
}

export function getSession() {
  const token = getToken();
  if (!token) {
    return null;
  }

  try {
    const payload = decodeToken(token);
    if (payload.exp && Date.now() >= payload.exp * 1000) {
      clearToken();
      return null;
    }
    return {
      token,
      email: payload.sub,
      role: payload.role,
    };
  } catch {
    clearToken();
    return null;
  }
}
