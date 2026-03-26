import { PortalLayout } from "@/components/layout/PortalLayout";

const adminNav = [
  { href: "/admin/reports", label: "Reports" },
  { href: "/admin/upload", label: "Upload" },
  { href: "/admin/interviewers", label: "Interviewers" },
  { href: "/admin/assignments", label: "Assignments" },
];

export function AdminShell({ children }: { children: React.ReactNode }) {
  return (
    <PortalLayout
      role="admin"
      loginHref="/admin/login"
      title="Admin Portal"
      navItems={adminNav}
    >
      {children}
    </PortalLayout>
  );
}
