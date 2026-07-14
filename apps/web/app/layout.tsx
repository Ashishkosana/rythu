import type { Metadata, Viewport } from "next";
import { Geist, Noto_Sans_Telugu } from "next/font/google";
import BottomNav from "@/components/BottomNav";
import Welcome from "@/components/Welcome";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

// Crisp, consistent Telugu rendering — the app's primary language.
const notoTelugu = Noto_Sans_Telugu({
  variable: "--font-telugu",
  subsets: ["telugu"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Rythu — వాతావరణం",
  description: "Honest weather + farming advice for Bhupalpally farmers.",
  appleWebApp: {
    capable: true,
    title: "Rythu",
    statusBarStyle: "default",
  },
};

export const viewport: Viewport = {
  themeColor: "#15803d",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${notoTelugu.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {children}
        <BottomNav />
        <Welcome />
      </body>
    </html>
  );
}
