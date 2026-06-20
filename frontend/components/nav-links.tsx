"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Today" },
  { href: "/standings", label: "Standings" },
  { href: "/fixtures", label: "Fixtures" },
  { href: "/archive", label: "Archive" },
  { href: "/changelog", label: "Changelog" },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function NavLinks() {
  const pathname = usePathname();
  return (
    <div className="flex gap-5 text-sm font-medium whitespace-nowrap" style={{ color: "#A9B6D4" }}>
      {LINKS.map((link) => {
        const active = isActive(pathname, link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={active ? "page" : undefined}
            className="transition-colors hover:text-white"
            style={{
              color: active ? "#FFFFFF" : "inherit",
              borderBottom: active ? "2px solid #2D6BF6" : "2px solid transparent",
              paddingBottom: "2px",
            }}
          >
            {link.label}
          </Link>
        );
      })}
    </div>
  );
}
