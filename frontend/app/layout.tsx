import type { Metadata } from "next";
import { Nunito_Sans } from "next/font/google";
import "./globals.css";

const nunitoSans = Nunito_Sans({
  variable: "--font-ui",
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "PuebloLindo | Tickets",
  description: "Panel de tickets y auditoria para Customer Success",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <html lang="es" className={`${nunitoSans.variable} h-full antialiased`}><body className="min-h-full">{children}</body></html>;
}
