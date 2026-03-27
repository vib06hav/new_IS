"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { login } from "@/lib/api";
import { signOut } from "@/lib/auth";
import type { UserRole } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

type LoginFormProps = {
  role: UserRole;
  title: string;
  successHref: string;
};

export function LoginForm({ role, title, successHref }: LoginFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    <Card title={title} description="Use the credentials issued for this role.">
      <form className="space-y-4" onSubmit={handleSubmit}>
        <Input label="Email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
        <Input label="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        {error ? <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
        <div className="flex items-center justify-between gap-4">
          <Button disabled={submitting || !email || !password} type="submit">
            {submitting ? "Signing in..." : "Sign in"}
          </Button>
          <Link className="text-sm text-muted underline" href="/">
            Back to landing
          </Link>
        </div>
      </form>
    </Card>
  );
}
