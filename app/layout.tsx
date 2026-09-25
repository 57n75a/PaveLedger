import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PaveLedger | Road intelligence",
  description: "Road safety investigations and repair accountability. Private demonstration.",
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
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
