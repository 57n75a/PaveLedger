import type { Metadata } from "next";
import "./globals.css";
import { LangProvider } from "@/lib/i18n";
import { instance } from "@/lib/instance";

const meta = instance.meta[instance.defaultLang] || instance.meta.en!;
const HTML_LANG = { sr: "sr-Latn", en: "en", fr: "fr-CA" } as const;

export const metadata: Metadata = {
  title: meta.title,
  description: meta.description,
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
    <html lang={HTML_LANG[instance.defaultLang]}>
      <body className="antialiased"><LangProvider>{children}</LangProvider></body>
    </html>
  );
}
