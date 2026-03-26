import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AG Interview Standardiser",
  description: "Barebones admin and interviewer frontend."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
