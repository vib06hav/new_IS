import { LoginForm } from "@/components/LoginForm";

export default function InterviewerLoginPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-xl items-center px-6 py-10">
      <LoginForm role="interviewer" title="Interviewer Login" successHref="/interviewer/dashboard" />
    </main>
  );
}
