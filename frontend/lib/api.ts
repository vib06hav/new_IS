import type {
  ApplicationDetailAdmin,
  ApplicationDetailInterviewer,
  ApplicationListItem,
  ApplicationUploadResponse,
  AssignmentListItem,
  DraftMutationResponse,
  InterviewerListItem,
  TokenResponse,
} from "@/lib/types";

async function parseError(response: Response) {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data?.detail)) {
      return data.detail
        .map((item: { loc?: Array<string | number>; msg?: string }) => {
          const field = item.loc?.[item.loc.length - 1];
          if (field && item.msg) {
            return `${String(field)}: ${item.msg}`;
          }
          return item.msg || "Validation error";
        })
        .join(", ");
    }
  } catch {
    // Fall back to status text below.
  }
  return `${response.status} ${response.statusText}`;
}

async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, init);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

function authHeaders(token: string) {
  return {
    Authorization: `Bearer ${token}`,
  };
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: body.toString(),
  });
}

export async function createInterviewer(payload: { name: string; email: string; password: string }) {
  return apiRequest("/auth/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ...payload,
      role: "interviewer",
    }),
  });
}

export async function fetchApplications(token: string, status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiRequest<ApplicationListItem[]>(`/applications${query}`, {
    headers: authHeaders(token),
  });
}

export async function fetchApplicationDetail<T extends ApplicationDetailAdmin | ApplicationDetailInterviewer>(
  token: string,
  applicationId: string,
) {
  return apiRequest<T>(`/applications/${applicationId}`, {
    headers: authHeaders(token),
  });
}

export async function uploadApplication(token: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<ApplicationUploadResponse>("/applications/upload", {
    method: "POST",
    headers: authHeaders(token),
    body: formData,
  });
}

export async function retryApplication(token: string, applicationId: string) {
  return apiRequest<ApplicationListItem>(`/applications/${applicationId}/retry`, {
    method: "POST",
    headers: authHeaders(token),
  });
}

export async function assignApplication(token: string, applicationId: string, interviewerId: string) {
  return apiRequest<ApplicationListItem>(`/applications/${applicationId}/assign`, {
    method: "POST",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ interviewer_id: interviewerId }),
  });
}

export async function reassignApplication(token: string, applicationId: string, interviewerId: string) {
  return apiRequest<ApplicationListItem>(`/applications/${applicationId}/assign`, {
    method: "PUT",
    headers: {
      ...authHeaders(token),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ interviewer_id: interviewerId }),
  });
}

export async function fetchInterviewers(token: string) {
  return apiRequest<InterviewerListItem[]>("/users/interviewers", {
    headers: authHeaders(token),
  });
}

export async function deleteInterviewer(token: string, userId: string) {
  return apiRequest<void>(`/users/${userId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export async function fetchAssignments(token: string) {
  return apiRequest<AssignmentListItem[]>("/assignments", {
    headers: authHeaders(token),
  });
}

export async function fetchMyApplications(token: string) {
  return apiRequest<ApplicationListItem[]>("/me/applications", {
    headers: authHeaders(token),
  });
}

export async function generateDraft(token: string, applicationId: string) {
  return apiRequest<DraftMutationResponse>(`/applications/${applicationId}/generate`, {
    method: "POST",
    headers: authHeaders(token),
  });
}

export async function publishDraft(token: string, applicationId: string) {
  return apiRequest<DraftMutationResponse>(`/applications/${applicationId}/publish`, {
    method: "POST",
    headers: authHeaders(token),
  });
}
