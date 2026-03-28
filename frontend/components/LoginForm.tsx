"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { login } from "@/lib/api";
import { signOut } from "@/lib/auth";
import type { UserRole } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

type LoginFormProps = {
  role: UserRole;
  title: string;
  successHref: string;
};

const roleCopy: Record<UserRole, { eyebrow: string; detail: string }> = {
  admin: {
    eyebrow: "Admin Gateway",
    detail: "Upload, assign, and monitor admissions briefs.",
  },
  interviewer: {
    eyebrow: "Interviewer Gateway",
    detail: "Review assigned applications and prepare interview briefs.",
  },
};

export function LoginForm({ role, title, successHref }: LoginFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const copy = roleCopy[role];

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const response = await login(email, password);
      if (response.user.role !== role) {
        await signOut();
        throw new Error(`This account does not belong in the ${role} portal.`);
      }

      router.replace(successHref);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Login failed.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="clay-card w-full max-w-md p-8 shadow-[var(--card-shadow)]">
      <div className="mb-6 space-y-2">
        <p className="text-[11px] font-bold uppercase tracking-[0.22em] text-slate-400">{copy.eyebrow}</p>
        <h2 className="text-2xl font-bold tracking-tight text-brand-deep">{title}</h2>
        <p className="text-sm leading-6 text-slate-600">{copy.detail}</p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <Input label="Email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
        <Input label="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        {error ? (
          <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-700">{error}</p>
        ) : null}
        <div className="flex flex-col gap-3 pt-2">
          <Button className="w-full" disabled={submitting || !email || !password} type="submit">
            {submitting ? "Signing in..." : "Sign in"}
          </Button>
          <Link className="text-center text-sm font-medium text-slate-500 hover:text-brand-accent transition-colors" href="/">
            Back to landing
          </Link>
        </div>
      </form>
    </div>
  );
}
