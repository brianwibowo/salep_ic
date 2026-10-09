import type { Metadata } from "next";
import { Poppins, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ProvidersWrapper } from "../providers/provider";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "SALEP | Sales Intelligence",
  description: "Temukan dan kelola prospek penjualan.",
};

const poppins = Poppins({
  variable: "--font-poppins",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
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
        className={`${poppins.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <ProvidersWrapper>
          <Toaster />
          {children}
        </ProvidersWrapper>
      </body>
    </html>
  );
}
