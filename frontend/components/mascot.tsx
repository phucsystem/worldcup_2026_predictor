// Original host-nation supporter characters (moose=Canada, jaguar=Mexico,
// eagle=USA). Deliberately NOT the trademarked FIFA 2026 mascots.
type MascotKind = "moose" | "jaguar" | "eagle";

const PATHS: Record<MascotKind, React.ReactNode> = {
  moose: (
    <>
      <path d="M16 13 Q9 6 5 9 Q11 9 12 13 Q7 11 6 15 Q12 13 15 16Z" fill="#8a5a2b" />
      <path d="M32 13 Q39 6 43 9 Q37 9 36 13 Q41 11 42 15 Q36 13 33 16Z" fill="#8a5a2b" />
      <ellipse cx="13" cy="20" rx="3.4" ry="5" fill="#6a3f22" />
      <ellipse cx="35" cy="20" rx="3.4" ry="5" fill="#6a3f22" />
      <ellipse cx="24" cy="26" rx="12" ry="13" fill="#7a4a28" />
      <ellipse cx="24" cy="33" rx="8" ry="7" fill="#9a6638" />
      <ellipse cx="24" cy="33.5" rx="3.4" ry="2.5" fill="#33200f" />
      <circle cx="19" cy="24" r="2.2" fill="#1a0f08" />
      <circle cx="29" cy="24" r="2.2" fill="#1a0f08" />
      <circle cx="19.7" cy="23.3" r="0.8" fill="#fff" />
      <circle cx="29.7" cy="23.3" r="0.8" fill="#fff" />
      <circle cx="14" cy="30" r="2" fill="#D80621" opacity="0.5" />
      <circle cx="34" cy="30" r="2" fill="#D80621" opacity="0.5" />
    </>
  ),
  jaguar: (
    <>
      <path d="M12 13 L19 20 L10 22Z" fill="#c98a2e" />
      <path d="M36 13 L29 20 L38 22Z" fill="#c98a2e" />
      <path d="M13 16 L17 20 L12 21Z" fill="#5a3a12" />
      <path d="M35 16 L31 20 L36 21Z" fill="#5a3a12" />
      <ellipse cx="24" cy="26" rx="13" ry="12" fill="#e0a93f" />
      <circle cx="14" cy="22" r="1.5" fill="#5a3a12" />
      <circle cx="34" cy="22" r="1.5" fill="#5a3a12" />
      <circle cx="12.5" cy="29" r="1.2" fill="#5a3a12" />
      <circle cx="35.5" cy="29" r="1.2" fill="#5a3a12" />
      <ellipse cx="24" cy="31" rx="8" ry="6" fill="#f3d79a" />
      <circle cx="19" cy="24" r="2.4" fill="#1c3a1c" />
      <circle cx="29" cy="24" r="2.4" fill="#1c3a1c" />
      <circle cx="19.8" cy="23.2" r="0.8" fill="#fff" />
      <circle cx="29.8" cy="23.2" r="0.8" fill="#fff" />
      <path d="M21.5 29 L26.5 29 L24 31.6Z" fill="#2BD37E" />
    </>
  ),
  eagle: (
    <>
      <path d="M11 18 Q14 11 18 16 Q20 10 24 15 Q28 10 30 16 Q34 11 37 18Z" fill="#dfe7f5" />
      <ellipse cx="24" cy="24" rx="13" ry="13" fill="#f4f7ff" />
      <path d="M13 21 Q19 18 23 22.5" stroke="#1b3a6b" strokeWidth="2.4" fill="none" strokeLinecap="round" />
      <path d="M35 21 Q29 18 25 22.5" stroke="#1b3a6b" strokeWidth="2.4" fill="none" strokeLinecap="round" />
      <circle cx="18" cy="24.5" r="2.4" fill="#15233f" />
      <circle cx="30" cy="24.5" r="2.4" fill="#15233f" />
      <circle cx="18.8" cy="23.7" r="0.8" fill="#fff" />
      <circle cx="30.8" cy="23.7" r="0.8" fill="#fff" />
      <path d="M21 28 L27 28 L24 37 Q22.5 33 21 28Z" fill="#F4B740" />
      <path d="M21 28 L27 28 L24 30.5Z" fill="#d99a1f" />
      <circle cx="12.5" cy="28" r="1.9" fill="#2D6BF6" opacity="0.45" />
      <circle cx="35.5" cy="28" r="1.9" fill="#2D6BF6" opacity="0.45" />
    </>
  ),
};

export default function Mascot({
  kind,
  size = 44,
  idle = false,
  className = "",
}: {
  kind: MascotKind;
  size?: number;
  idle?: boolean;
  className?: string;
}) {
  return (
    <span
      className={`mascot-av ${kind}${idle ? " idle" : ""}${className ? ` ${className}` : ""}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 48 48">{PATHS[kind]}</svg>
    </span>
  );
}

export type { MascotKind };
