"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowRight, ShieldCheck } from "lucide-react";
import type { UserRole } from "@/lib/types";

type LoginFormProps = {
  role: UserRole;
  title: string;
};

const roleCopy: Record<UserRole, { eyebrow: string; detail: string }> = {
  admin: {
    eyebrow: "Admin Gateway",
    detail: "Continue to the secure WorkOS sign-in screen. You'll be redirected once your admin access is confirmed.",
  },
  interviewer: {
    eyebrow: "Interviewer Gateway",
    detail: "Use the email address you were invited with. You'll continue to the secure WorkOS sign-in screen and will be redirected once access is confirmed.",
  },
};

export function LoginForm({ role, title }: LoginFormProps) {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");
  const copy = roleCopy[role];

  return (
    <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-2xl">
      <div className="mb-6 space-y-2">
        <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-slate-400">{copy.eyebrow}</p>
        <h2 className="text-2xl font-bold tracking-tight text-brand-deep">{title}</h2>
        <p className="text-sm leading-6 text-slate-600">{copy.detail}</p>
      </div>

      <div className="space-y-4">
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</p>
        ) : null}

        <a
          className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-300"
          href={`/api/auth/login?portal=${role}`}
        >
          Continue to sign in
          <ArrowRight className="size-4" />
        </a>

        <Link className="block text-center text-sm font-medium text-slate-500 transition-colors hover:text-brand-accent" href="/">
          Back to landing
        </Link>
      </div>
    </div>
  );
}
