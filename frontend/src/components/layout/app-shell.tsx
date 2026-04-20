"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, History, Home, Menu, ShieldCheck, X } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type AppShellProps = {
  children: React.ReactNode;
};

type NavItem = {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
};

const navItems: NavItem[] = [
  { href: "/home", label: "Home", icon: Home },
  { href: "/history", label: "Historial", icon: History },
  { href: "/reports", label: "Reportes", icon: BarChart3 },
];

function SidebarContent({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  return (
    <>
      <div className="mb-8 space-y-2">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-white/70">Mesa de Ayuda</p>
        <h1 className="text-2xl font-semibold text-white">Gestion Operativa</h1>
        <p className="text-sm text-white/75">Customer Success y auditoria de casos</p>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                active
                  ? "bg-[var(--accent-500)] text-white shadow"
                  : "text-white/90 hover:bg-white/10 hover:text-white"
              )}
            >
              <Icon className="h-4 w-4" />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto rounded-lg border border-white/15 bg-white/10 p-3 text-xs text-white/80">
        <div className="mb-2 flex items-center gap-2 text-white">
          <ShieldCheck className="h-4 w-4" />
          <span className="font-semibold">Auditoria activa</span>
        </div>
        <p>Revisa tickets cerrados en Historial para trazabilidad del cierre.</p>
      </div>
    </>
  );
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const activeSection = useMemo(() => {
    if (pathname === "/reports") {
      return "Reportes";
    }
    if (pathname === "/history") {
      return "Historial";
    }
    return "Home";
  }, [pathname]);

  return (
    <div className="min-h-screen bg-[#f4f5f8] md:grid md:grid-cols-[250px_1fr]">
      <aside className="hidden border-r border-[#2b0a72] bg-[linear-gradient(180deg,#3A108C_0%,#2A0A66_100%)] p-6 md:flex md:flex-col">
        <SidebarContent pathname={pathname} />
      </aside>

      <div className="flex min-h-screen flex-col">
        <header className="sticky top-0 z-20 flex items-center justify-between border-b border-[#2b0a72] bg-[linear-gradient(180deg,#3A108C_0%,#2A0A66_100%)] px-4 py-3 backdrop-blur md:hidden">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-white/70">PuebloLindo</p>
            <p className="text-sm font-semibold text-white">{activeSection}</p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="text-white hover:bg-white/15 hover:text-white"
            onClick={() => setMobileOpen(true)}
            aria-label="Abrir menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </header>

        {mobileOpen && (
          <div className="fixed inset-0 z-30 flex md:hidden">
            <button
              className="h-full flex-1 bg-black/30"
              onClick={() => setMobileOpen(false)}
              aria-label="Cerrar menu"
            />
            <aside className="flex h-full w-[82%] max-w-[320px] flex-col border-l border-[#2b0a72] bg-[linear-gradient(180deg,#3A108C_0%,#2A0A66_100%)] p-5">
              <div className="mb-3 flex justify-end">
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-white hover:bg-white/15 hover:text-white"
                  onClick={() => setMobileOpen(false)}
                  aria-label="Cerrar"
                >
                  <X className="h-5 w-5" />
                </Button>
              </div>
              <SidebarContent pathname={pathname} onNavigate={() => setMobileOpen(false)} />
            </aside>
          </div>
        )}

        <main className="flex-1 px-4 py-6 md:px-8 md:py-8">{children}</main>
      </div>
    </div>
  );
}
