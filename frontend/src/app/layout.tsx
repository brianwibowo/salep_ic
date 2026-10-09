import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ProvidersWrapper } from "../providers/provider";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "SALEP | Sales Intelligence",
  description: "Temukan dan kelola prospek penjualan.",
};

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ProvidersWrapper>
          <Toaster />
          {children}
        </ProvidersWrapper>
      </body>
    </html>
  );
}
