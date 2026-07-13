"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/workspace", index: "01", label: "工作台" },
  { href: "/research", index: "02", label: "我的调研" },
  { href: "/knowledge", index: "03", label: "知识库" },
  { href: "/experts", index: "04", label: "专家公会" },
  { href: "/intelligence", index: "05", label: "竞争情报中心" }
];

function isActive(pathname, href) {
  if (href === "/workspace") {
    return pathname === "/" || pathname === "/workspace";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children }) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link href="/workspace" className="flex items-center gap-3 px-2">
          <div className="brand-mark">V</div>
          <div className="brand-copy">
            <strong className="block text-[15px] font-semibold leading-tight">Verity</strong>
            <span className="mt-1 block text-xs text-[color:var(--muted)]">Evidence Research Console</span>
          </div>
        </Link>

        <nav className="grid gap-1" aria-label="Primary navigation">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className={`nav-link ${isActive(pathname, item.href) ? "active" : ""}`}>
              <span className="w-[18px] text-center text-xs text-[color:var(--sage)]">{item.index}</span>
              <span className="nav-label">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer mt-auto grid gap-3">
          <div className="panel p-3">
            <div className="flex justify-between text-xs text-[color:var(--muted)]">
              <span>Data source</span>
              <strong className="text-[color:var(--sage)]">mock</strong>
            </div>
            <p className="mt-2 text-xs leading-5 text-[color:var(--muted)]">当前仅展示 Mock 形态，不代表真实抓取。</p>
          </div>
          <div className="flex items-center gap-3 px-2">
            <div className="grid h-9 w-9 place-items-center rounded-full bg-[color:var(--sage)] text-xs font-semibold text-white">林</div>
            <div>
              <strong className="block text-[13px] font-semibold">林研究员</strong>
              <span className="text-xs text-[color:var(--muted)]">PM Candidate</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="min-w-0">
        <header className="topbar">
          <span className="text-[13px] text-[color:var(--muted)]">Verity P1 Mock Shell</span>
          <span className="chip chip-sage">Mock data · 非真实在线抓取</span>
        </header>
        <div className="page">{children}</div>
      </main>
    </div>
  );
}
