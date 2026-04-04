import type {
  ApplicationDetailAdmin,
  ApplicationDetailInterviewer,
  ApplicationListItem,
  ApplicationUploadResponse,
  AssignmentListItem,
  InterviewerAssignmentSavePayload,
  InterviewerAssignmentSummary,
  DraftMutationResponse,
  InterviewerListItem,
  InterviewerUpdatePayload,
  PasswordChangePayload,
  SelfPasswordChangePayload,
  SessionResponse,
} from "@/lib/types";
import { getCsrfToken } from "@/lib/csrf";

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
  const headers = new Headers(init.headers);
  const method = (init.method || "GET").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS", "TRACE"].includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers.set("X-CSRF-Token", csrfToken);
    }
  }

  const response = await fetch(`/api${path}`, {
    credentials: "same-origin",
    ...init,
    headers,
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  return apiRequest<SessionResponse>("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: body.toString(),
  });
}

export async function createInterviewer(payload: { name: string; email: string; password: string }) {
  return apiRequest("/users/interviewers", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchSourcePdf(applicationId: string) {
  const response = await fetch(`/api/applications/${applicationId}/source-pdf`, {
    credentials: "same-origin",
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.blob();
}

export async function fetchApplications(status?: string) {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiRequest<ApplicationListItem[]>(`/applications${query}`);
}

export async function fetchApplicationDetail<T extends ApplicationDetailAdmin | ApplicationDetailInterviewer>(
  applicationId: string,
) {
  return apiRequest<T>(`/applications/${applicationId}`);
}

export async function uploadApplication(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest<ApplicationUploadResponse>("/applications/upload", {
    method: "POST",
    body: formData,
  });
}

export async function retryApplication(applicationId: string) {
  return apiRequest<ApplicationListItem>(`/applications/${applicationId}/retry`, {
    method: "POST",
  });
}

export async function hideApplication(applicationId: string) {
  return apiRequest<ApplicationListItem>(`/applications/${applicationId}/hide`, {
    method: "POST",
  });
}

export async function unhideApplication(applicationId: string) {
  return apiRequest<ApplicationListItem>(`/applications/${applicationId}/unhide`, {
    method: "POST",
  });
}

export async function removeQueuedApplication(applicationId: string) {
  return apiRequest<void>(`/applications/${applicationId}/queue`, {
    method: "DELETE",
  });
}

export async function assignApplication(applicationId: string, interviewerId: string) {
  return apiRequest<ApplicationListItem>(`/applications/${applicationId}/assign`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ interviewer_id: interviewerId }),
  });
}

export async function reassignApplication(applicationId: string, interviewerId: string) {
  return apiRequest<ApplicationListItem>(`/applications/${applicationId}/assign`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ interviewer_id: interviewerId }),
  });
}

export async function fetchInterviewers() {
  return apiRequest<InterviewerListItem[]>("/users/interviewers");
}

export async function fetchInterviewerAssignmentSummary(userId: string) {
  return apiRequest<InterviewerAssignmentSummary>(`/users/interviewers/${userId}/assignments`);
}

export async function saveInterviewerAssignments(userId: string, payload: InterviewerAssignmentSavePayload) {
  return apiRequest<InterviewerAssignmentSummary>(`/users/interviewers/${userId}/assignments`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function deleteInterviewer(userId: string) {
  return apiRequest<void>(`/users/${userId}`, {
    method: "DELETE",
  });
}

export async function updateInterviewer(userId: string, payload: InterviewerUpdatePayload) {
  return apiRequest(`/users/interviewers/${userId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function updateInterviewerPassword(userId: string, payload: PasswordChangePayload) {
  return apiRequest(`/users/interviewers/${userId}/password`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export async function fetchAssignments() {
  return apiRequest<AssignmentListItem[]>("/assignments");
}

export async function fetchMyApplications() {
  return apiRequest<ApplicationListItem[]>("/me/applications");
}

export async function generateDraft(applicationId: string) {
  return apiRequest<DraftMutationResponse>(`/applications/${applicationId}/generate`, {
    method: "POST",
  });
}

export async function publishDraft(applicationId: string) {
  return apiRequest<DraftMutationResponse>(`/applications/${applicationId}/publish`, {
    method: "POST",
  });
}

export async function changeMyPassword(payload: SelfPasswordChangePayload) {
  return apiRequest<SessionResponse>("/auth/change-password", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
