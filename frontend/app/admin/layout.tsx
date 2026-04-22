import { PortalSessionProvider } from "@/components/auth/PortalSessionProvider";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <PortalSessionProvider loginHref="/admin/login" portal="admin">
      {children}
    </PortalSessionProvider>
  );
}
