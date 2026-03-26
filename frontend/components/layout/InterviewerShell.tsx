import { PortalLayout } from "@/components/layout/PortalLayout";

const interviewerNav = [{ href: "/interviewer/dashboard", label: "Dashboard" }];

export function InterviewerShell({ children }: { children: React.ReactNode }) {
  return (
    <PortalLayout
      role="interviewer"
      loginHref="/interviewer/login"
      title="Interviewer Portal"
      navItems={interviewerNav}
    >
      {children}
    </PortalLayout>
  );
}
