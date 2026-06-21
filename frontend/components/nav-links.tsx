"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Today" },
  { href: "/standings", label: "Standings" },
  { href: "/fixtures", label: "Fixtures" },
  { href: "/changelog", label: "Changelog" },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function NavLinks() {
  const pathname = usePathname();
  return (
    <div className="nav-links">
      {LINKS.map((link) => {
        const active = isActive(pathname, link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={active ? "page" : undefined}
            className={active ? "nav-link active" : "nav-link"}
          >
            {link.label}
          </Link>
        );
      })}
    </div>
  );
}
