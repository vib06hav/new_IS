import { PortalSessionProvider } from "@/components/auth/PortalSessionProvider";

export default function InterviewerLayout({ children }: { children: React.ReactNode }) {
  return (
    <PortalSessionProvider loginHref="/interviewer/login" portal="interviewer">
      {children}
    </PortalSessionProvider>
  );
}
