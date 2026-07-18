"use client";

import Link from "next/link";
import { BookOpen, Home, Search, Target, Users } from "lucide-react";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/workspace", label: "工作台", Icon: Home },
  { href: "/research", label: "我的调研", Icon: Search },
  { href: "/knowledge", label: "知识库", Icon: BookOpen },
  { href: "/experts", label: "专家公会", Icon: Users },
  { href: "/intelligence", label: "竞争情报中心", Icon: Target }
];

function isActive(pathname, href) {
  if (href === "/workspace") return pathname === "/" || pathname === "/workspace";
  if (href === "/research") return pathname === "/research" || pathname.startsWith("/research/") || pathname.startsWith("/reports/");
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function AppShell({ children }) {
  const pathname = usePathname();

  return (
    <div className="app app-shell">
      <aside className="sidebar">
        <Link href="/workspace" className="brand" aria-label="Verity 工作台">
          <strong>Verity</strong>
        </Link>

        <nav className="nav" aria-label="Primary navigation">
          {navItems.map(({ href, label, Icon }) => (
            <Link key={href} href={href} className={isActive(pathname, href) ? "active" : ""}>
              <Icon className="nav-icon" aria-hidden="true" />
              <span>{label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar-meta">
          <div className="small-panel">
            <div className="meta-row"><span>Workspace token</span><strong>58%</strong></div>
            <div className="meter" aria-label="Workspace token 58%"><span /></div>
          </div>
          <div className="profile">
            <div className="avatar">林</div>
            <div>
              <strong>林研究员</strong>
              <span>PM Candidate</span>
            </div>
          </div>
        </div>
      </aside>

      <main className="main">
        <div className="page">{children}</div>
      </main>
    </div>
  );
}
