import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { UserProvider } from "@/lib/user-context";
import Navigation from "@/components/navigation";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: 'cool_squad',
  description: 'chat with your robot friends :)',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-900 text-gray-100`}>
        <UserProvider>
          <div className="flex flex-col min-h-screen">
            <Navigation />
            <main className="flex-1 container mx-auto p-4 overflow-hidden">
              {children}
            </main>
            <footer className="bg-gray-800 py-3 text-center text-sm text-gray-400 mt-2">
              cool_squad v0.1.0 - chat with your robot friends :)
            </footer>
          </div>
        </UserProvider>
      </body>
    </html>
  );
}
