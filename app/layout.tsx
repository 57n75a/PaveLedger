import type { Metadata } from "next";
import "./globals.css";
import { LangProvider } from "@/lib/i18n";

export const metadata: Metadata = {
  title: "PaveLedger | Inteligencija puteva",
  description: "Prijave za bezbednost puteva i odgovornost za popravke. Privatna demonstracija.",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="sr-Latn">
      <body className="antialiased"><LangProvider>{children}</LangProvider></body>
    </html>
  );
}
