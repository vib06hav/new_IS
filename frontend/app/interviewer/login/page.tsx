import { Suspense } from "react";
import { LoginForm } from "@/components/LoginForm";

export default function InterviewerLoginPage() {
  return (
    <main className="auth-bg min-h-screen">
      <div className="flex min-h-screen flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
          <div className="flex items-center space-x-2">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-brand-accent to-brand-hover shadow-sm">
              <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                />
              </svg>
              <span className="absolute -bottom-1 -right-1 rounded border border-slate-200 bg-white px-1 text-[10px] font-bold text-brand-deep">
                IS
              </span>
            </div>
            <span className="text-xl font-semibold tracking-tight text-brand-deep">Interview Standardiser</span>
          </div>
        </header>

        <div className="flex flex-1 items-center justify-center p-6">
          <div className="grid w-full max-w-6xl gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50/70 px-4 py-2">
                <div className="h-1.5 w-1.5 rounded-full bg-blue-700" />
                <span className="text-[10px] font-bold uppercase tracking-widest text-blue-900">Interview Standardiser</span>
              </div>
              <div>
                <h1 className="mb-6 text-5xl font-black leading-[1.1] tracking-tight text-slate-800">Interviewer Portal</h1>
                <p className="max-w-xl text-lg leading-[1.6] text-slate-600">
                  Review completed reports, inspect the source package, and prepare interviews with traceable evidence.
                </p>
              </div>
            </div>
            <Suspense fallback={<div className="clay-card w-full max-w-md p-8 shadow-[var(--card-shadow)]">Loading sign-in…</div>}>
              <LoginForm role="interviewer" title="Interviewer Login" />
            </Suspense>
          </div>
        </div>
      </div>
    </main>
  );
}
