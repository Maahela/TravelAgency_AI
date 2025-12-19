import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "JAKEmail Admin | Hotel Intelligence",
  description: "Advanced hotel rate extraction & management console",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body 
        className="antialiased font-sans selection:bg-accent/30 selection:text-white"
        suppressHydrationWarning
      >
        <div className="flex bg-background min-h-screen text-foreground overflow-hidden">
          <Sidebar />
          <main className="flex-1 h-screen overflow-y-auto overflow-x-hidden relative">
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent/5 blur-[120px] rounded-full -mr-48 -mt-48 pointer-events-none" />
            <div className="p-10 relative z-10 max-w-[1600px] mx-auto">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
