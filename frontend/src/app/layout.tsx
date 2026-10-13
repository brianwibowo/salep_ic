import type { Metadata } from "next";
import "./globals.css";
import { ProvidersWrapper } from "../providers/provider";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "SALEP | Sales Intelligence",
  description: "Temukan dan kelola prospek penjualan.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <ProvidersWrapper>
          <Toaster />
          {children}
        </ProvidersWrapper>
      </body>
    </html>
  );
}
