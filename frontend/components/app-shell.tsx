"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { FileBarChart2, LayoutDashboard, ListChecks, Menu, Plus, Users, X } from "lucide-react";
import { Logo } from "./logo";
import { ButtonLink, cn } from "./ui";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/interviews", label: "Interviews", icon: ListChecks },
  { href: "/candidates", label: "Candidates", icon: Users },
  { href: "/reports", label: "Reports", icon: FileBarChart2 },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav className="space-y-0.5" aria-label="Main">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href) && pathname !== "/interviews/new");
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors",
              active ? "bg-ink/[0.06] text-ink" : "text-muted hover:bg-ink/[0.04] hover:text-ink",
            )}
          >
            <Icon className="size-4" aria-hidden />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

function EngineFooter() {
  return (
    <div className="rounded-lg border border-line bg-canvas p-3 text-xs text-muted">
      <p className="font-medium text-ink-2">Engineering demo</p>
      <p className="mt-1 leading-relaxed">
        Inference via Groq (open-weight gpt-oss-120b). Retrieval via Gemini embeddings + Supabase pgvector.
      </p>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-line bg-surface px-3 py-4 lg:flex">
        <div className="px-2.5 pb-6">
          <Logo href="/" />
        </div>
        <ButtonLink href="/interviews/new" size="sm" className="mb-5 w-full">
          <Plus className="size-4" aria-hidden /> Create interview
        </ButtonLink>
        <NavLinks />
        <div className="mt-auto">
          <EngineFooter />
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-line bg-surface/90 px-4 backdrop-blur lg:hidden">
          <Logo href="/" />
          <button
            className="rounded-lg p-2 text-ink-2 hover:bg-ink/5"
            onClick={() => setOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="size-5" />
          </button>
        </header>

        {open && (
          <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true">
            <div className="absolute inset-0 bg-ink/30" onClick={() => setOpen(false)} />
            <div className="absolute inset-y-0 left-0 flex w-72 flex-col bg-surface px-3 py-4 shadow-xl">
              <div className="flex items-center justify-between px-2.5 pb-6">
                <Logo href="/" />
                <button className="rounded-lg p-1.5 hover:bg-ink/5" onClick={() => setOpen(false)} aria-label="Close navigation">
                  <X className="size-5" />
                </button>
              </div>
              <ButtonLink href="/interviews/new" size="sm" className="mb-5 w-full" onClick={() => setOpen(false)}>
                <Plus className="size-4" aria-hidden /> Create interview
              </ButtonLink>
              <NavLinks onNavigate={() => setOpen(false)} />
              <div className="mt-auto">
                <EngineFooter />
              </div>
            </div>
          </div>
        )}

        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">{children}</main>
      </div>
    </div>
  );
}
