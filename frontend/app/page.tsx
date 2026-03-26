import { ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export default function LandingPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col justify-center gap-8 px-6 py-10">
      <div className="space-y-3">
        <p className="text-sm uppercase tracking-[0.2em] text-muted">AG Interview Standardiser</p>
        <h1 className="text-4xl font-semibold text-ink">Choose a portal.</h1>
        <p className="max-w-xl text-base text-muted">
          This frontend stays intentionally simple. Pick the admin or interviewer portal to continue.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Admin Portal" description="Upload, assign, monitor, and review applications.">
          <ButtonLink href="/admin/login">Open Admin Portal</ButtonLink>
        </Card>
        <Card title="Interviewer Portal" description="Review assigned applications, generate drafts, and publish reports.">
          <ButtonLink href="/interviewer/login" variant="secondary">
            Open Interviewer Portal
          </ButtonLink>
        </Card>
      </div>
    </main>
  );
}
