import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RRHH 360 AI",
  description: "Evaluaciones 360 multi-tenant con IA",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
