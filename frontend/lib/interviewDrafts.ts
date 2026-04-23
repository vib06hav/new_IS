import type { InterviewWorkspaceContent } from "@/lib/types";

export type InterviewDraftMode = "configure" | "postgame" | "overlay";

function getDraftKey(applicationId: string, mode: InterviewDraftMode) {
  return `interview-workspace-draft:${mode}:${applicationId}`;
}

export function readInterviewDraft(applicationId: string, mode: InterviewDraftMode) {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(getDraftKey(applicationId, mode));
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as InterviewWorkspaceContent;
  } catch {
    window.localStorage.removeItem(getDraftKey(applicationId, mode));
    return null;
  }
}

export function writeInterviewDraft(applicationId: string, mode: InterviewDraftMode, content: InterviewWorkspaceContent) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(getDraftKey(applicationId, mode), JSON.stringify(content));
}

export function clearInterviewDraft(applicationId: string, mode: InterviewDraftMode) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(getDraftKey(applicationId, mode));
}
