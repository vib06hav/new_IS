import { LoginForm } from "@/components/LoginForm";

export default function AdminLoginPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-xl items-center px-6 py-10">
      <LoginForm role="admin" title="Admin Login" successHref="/admin/reports" />
    </main>
  );
}
