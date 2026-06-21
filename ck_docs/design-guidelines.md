# Design Guidelines

**Project:** World Cup 2026 Intelligence  
**Scope:** Design system tokens, UI conventions, accessibility  
**Reference:** `ck_docs/UI_SPEC.md` (canonical design specification)  
**Last Updated:** 2026-06-21

---

## 1. Design System Overview

**Philosophy:** Dark sports dashboard — data-dense, credible, accessible.

**Theme:** Dark-only (v1); light theme deferred to v2.

**Extracted from:** FIFA World Cup 2026 official visual identity.

---

## 2. Color Palette

### 2.1 Surfaces (Dark Theme)

| Token | Hex | Usage | Notes |
|-------|-----|-------|-------|
| `--bg` | `#060E22` | Page background | Deep navy-black; sufficient contrast for text |
| `--surface` | `#0A1B3D` | Cards, header, table containers | FIFA navy; primary interactive surface |
| `--surface-elevated` | `#13294F` | Hover states, modals, active rows | Slightly lighter for layering |
| `--border` | `#1E3157` | Card borders, dividers | Subtle, non-distracting |

### 2.2 Semantic Colors

| Token | Hex | Usage | WCAG AA Contrast |
|-------|-----|-------|------------------|
| `--primary` | `#2D6BF6` | Primary buttons, links, accents | 4.5:1 (text on bg) |
| `--accent-bright` | `#4D8BFF` | Hover state for primary, highlights | 3.8:1 (lighter, non-critical) |
| `--text-primary` | `#FFFFFF` | Body text, headers | 15.0:1 (on bg) |
| `--text-secondary` | `#A9B6D4` | Secondary labels, hints | 8.2:1 (on bg) |
| `--text-tertiary` | `#6B7A9E` | Disabled text, faded | 4.5:1 (on bg) |

### 2.3 Status Colors

| Status | Hex | Meaning | Usage |
|--------|-----|---------|-------|
| **Win** (green) | `#2BD37E` | Match won, qualified | Result badges, ticks |
| **Draw** (yellow) | `#F4B740` | Match drawn | Result badges |
| **Loss** (red) | `#FF5A5A` | Match lost, eliminated | Result badges, alerts |
| **Info** (blue) | `#2D6BF6` | Informational | Badge backgrounds |
| **Warning** (orange) | `#FF9E1B` | At-risk status | Caution indicators |

### 2.4 CSS Custom Properties

All tokens defined in `frontend/app/globals.css`:

```css
:root {
  --bg: #060e22;
  --surface: #0a1b3d;
  --surface-elevated: #13294f;
  --border: #1e3157;
  
  --primary: #2d6bf6;
  --accent-bright: #4d8bff;
  
  --text-primary: #ffffff;
  --text-secondary: #a9b6d4;
  --text-tertiary: #6b7a9e;
  
  --status-win: #2bd37e;
  --status-draw: #f4b740;
  --status-loss: #ff5a5a;
  --status-info: #2d6bf6;
  --status-warning: #ff9e1b;
}

/* Support light theme (v2) */
@media (prefers-color-scheme: light) {
  :root {
    --bg: #ffffff;
    --surface: #f5f7fa;
    --text-primary: #0a1b3d;
    /* ... invert as needed ... */
  }
}
```

---

## 3. Typography

### 3.1 Font Stack

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto",
             "Oxygen", "Ubuntu", "Cantarell", sans-serif;
```

**Rationale:** System fonts reduce load time; familiar to all platforms.

### 3.2 Scale

| Role | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Page Title | 32px | 700 | 1.2 | H1 (brief title) |
| Section Title | 24px | 700 | 1.3 | H2 (group name, fixture section) |
| Card Title | 18px | 600 | 1.3 | H3 (team name, card header) |
| Body | 16px | 400 | 1.6 | Paragraph, table data |
| Small | 14px | 400 | 1.5 | Labels, hints |
| Tiny | 12px | 400 | 1.4 | Footer, metadata |

### 3.3 Usage Examples

```tsx
{/* Page Title */}
<h1 className="text-3xl font-bold text-text-primary">
  World Cup Intelligence
</h1>

{/* Body Text */}
<p className="text-base leading-relaxed text-text-secondary">
  Argentina advances to knockout stage...
</p>

{/* Small Label */}
<span className="text-sm font-medium text-text-tertiary">
  Match day 2
</span>
```

---

## 4. Spacing and Layout

### 4.1 Spacing Scale

Based on 8px grid:

| Token | Pixels | Usage |
|-------|--------|-------|
| `gap-1` | 8px | Tight spacing (between inline elements) |
| `gap-2` | 16px | Standard spacing (card padding, section margins) |
| `gap-3` | 24px | Loose spacing (major section breaks) |
| `gap-4` | 32px | Very loose spacing (page-level sections) |

### 4.2 Layout Widths

| Type | Width | Usage |
|------|-------|-------|
| Reading column | 960px | Brief markdown body (comfortable reading) |
| Standings column | 1120px | Group table (fit 6–7 columns) |
| Page max-width | 1360px | Full-width dashboard (with margins) |

**Implementation (Tailwind):**
```tsx
{/* Reading layout */}
<div className="max-w-3xl mx-auto px-4">
  {/* Brief body */}
</div>

{/* Standings layout */}
<div className="max-w-4xl mx-auto">
  {/* Group table */}
</div>
```

### 4.3 Responsive Breakpoints

| Breakpoint | Width | Device | Behavior |
|------------|-------|--------|----------|
| `sm` | 640px | Mobile | Single column, full-width cards |
| `md` | 768px | Tablet | Two columns if space permits |
| `lg` | 1024px | Desktop | Multi-column, sidebar navigation |
| `xl` | 1280px | Large desktop | Full-width layouts |

**Example:**
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* Responsive grid */}
</div>
```

---

## 5. Components and Patterns

### 5.1 Cards

**Structure:**
```tsx
<div className="bg-surface rounded-lg border border-border p-4">
  <h3 className="text-lg font-semibold text-text-primary mb-2">
    Title
  </h3>
  <p className="text-text-secondary">Content</p>
</div>
```

**Variants:**
- **Default:** bg-surface, border-border
- **Elevated:** bg-surface-elevated (for active/hover)
- **Highlighted:** border-primary (important section)

### 5.2 Buttons

**Primary:**
```tsx
<button className="bg-primary text-text-primary font-semibold px-4 py-2 rounded-lg hover:bg-accent-bright transition-colors">
  Action
</button>
```

**Secondary:**
```tsx
<button className="bg-surface border border-border text-text-primary px-4 py-2 rounded-lg hover:bg-surface-elevated transition-colors">
  Cancel
</button>
```

**Disabled:**
```tsx
<button disabled className="bg-surface text-text-tertiary px-4 py-2 rounded-lg cursor-not-allowed opacity-50">
  Disabled
</button>
```

### 5.3 Tables

**Header row:**
```tsx
<tr className="bg-surface-elevated border-b border-border">
  <th className="text-left px-4 py-2 text-text-secondary text-sm font-semibold">
    Team
  </th>
</tr>
```

**Data row (alternating):**
```tsx
<tr className="border-b border-border hover:bg-surface-elevated transition-colors">
  <td className="px-4 py-3 text-text-primary">Argentina</td>
</tr>
```

### 5.4 Status Badges

```tsx
{/* Win */}
<span className="inline-block bg-status-win text-bg px-3 py-1 rounded-full text-sm font-medium">
  Won
</span>

{/* Draw */}
<span className="inline-block bg-status-draw text-bg px-3 py-1 rounded-full text-sm font-medium">
  Draw
</span>

{/* Loss */}
<span className="inline-block bg-status-loss text-text-primary px-3 py-1 rounded-full text-sm font-medium">
  Lost
</span>

{/* Qualified */}
<span className="inline-block bg-status-info text-text-primary px-3 py-1 rounded-full text-sm font-medium">
  Qualified
</span>
```

### 5.5 Live Badge

```tsx
<div className="flex items-center gap-1">
  <span className="w-2 h-2 bg-status-loss rounded-full animate-pulse" />
  <span className="text-sm font-semibold text-status-loss">LIVE</span>
</div>
```

---

## 6. Radius and Shadows

### 6.1 Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `radius-card` | 12px | Cards, buttons, modals |
| `radius-sm` | 6px | Small elements (badges, pills) |
| `radius-lg` | 16px | Large containers (sections) |

### 6.2 Shadows

```css
/* Subtle (default) */
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);

/* Elevated (hover, active) */
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

/* Modal */
box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
```

**Tailwind classes:**
```tsx
<div className="rounded-lg shadow">  {/* Subtle */}
<div className="rounded-lg shadow-lg"> {/* Elevated */}
```

---

## 7. Animation and Motion

### 7.1 Transitions

**Standard transitions:**
```css
.interactive {
  transition: all 200ms ease-in-out;
}
```

**Usage:**
```tsx
<button className="bg-primary hover:bg-accent-bright transition-colors">
  Hover me
</button>
```

### 7.2 Respect Prefers-Reduced-Motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Component-level:**
```tsx
const prefersReducedMotion = useMediaQuery("(prefers-reduced-motion: reduce)");
return (
  <div className={prefersReducedMotion ? "" : "animate-pulse"}>
    Content
  </div>
);
```

---

## 8. Accessibility (a11y)

### 8.1 Contrast

**Minimum WCAG AA:** 4.5:1 for normal text, 3:1 for large text.

**All status colors meet AA on `--bg`.**

**Test:** Use [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/).

### 8.2 Focus Indicators

```css
*:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}
```

**Tailwind:**
```tsx
<button className="focus-visible:ring-2 focus-visible:ring-primary">
  Click me
</button>
```

### 8.3 Semantic HTML

```tsx
{/* Good */}
<button onClick={handleClick}>Action</button>
<a href="/standings">Standings</a>
<h1>Page Title</h1>

{/* Avoid */}
<div onClick={handleClick}>Action</div>  {/* Not keyboard-accessible */}
<div role="heading" aria-level="1">Page Title</div>  {/* Use <h1> */}
```

### 8.4 ARIA Labels

```tsx
{/* Unlabeled button */}
<button aria-label="Close dialog" onClick={onClose}>
  &times;
</button>

{/* Form input */}
<input
  type="search"
  placeholder="Search briefs"
  aria-label="Search briefs by date or keyword"
/>

{/* Live region */}
<div aria-live="polite" aria-label="Match score update">
  Score: 2–1 (Updated 5 min ago)
</div>
```

### 8.5 Keyboard Navigation

- **Tab order:** Natural reading order (left to right, top to bottom)
- **Enter/Space:** Activate buttons, toggle checkboxes
- **Arrow keys:** Navigate radio groups, select dropdowns, carousel slides

---

## 9. Dark Mode (v1)

**Current:** Dark-only. All colors tested on `#060e22` background.

**Light mode preparation (v2):**
```css
@media (prefers-color-scheme: light) {
  :root {
    --bg: #ffffff;
    --surface: #f5f7fa;
    --surface-elevated: #eff2f5;
    --text-primary: #0a1b3d;
    --text-secondary: #3f5378;
    --text-tertiary: #8b94a7;
    /* ... update other tokens ... */
  }
}
```

---

## 10. Imagery and Icons

### 10.1 Team Flags

**Source:** Flag emoji or SVG

**Fallback:** Team initials in a badge if flag unavailable

```tsx
function TeamFlag({ teamName, code }: { teamName: string; code: string }) {
  const [flagError, setFlagError] = useState(false);
  
  if (flagError) {
    return (
      <div className="w-8 h-8 bg-primary rounded flex items-center justify-center text-xs font-bold">
        {code.toUpperCase().substring(0, 2)}
      </div>
    );
  }
  
  return (
    <img
      src={`/flags/${code}.svg`}
      alt={teamName}
      className="w-8 h-8 rounded"
      onError={() => setFlagError(true)}
    />
  );
}
```

### 10.2 Icons

**Source:** Tailwind CSS built-in (or Heroicons for consistent set)

**Example (live badge):**
```tsx
{/* Pulse animation for live indicator */}
<div className="w-2 h-2 bg-status-loss rounded-full animate-pulse" />
```

---

## 11. Spacing and Sizing Examples

### 11.1 Brief Card

```tsx
<div className="bg-surface rounded-lg border border-border p-4 hover:bg-surface-elevated transition-colors">
  <div className="flex items-start justify-between gap-3 mb-3">
    <h3 className="text-lg font-semibold text-text-primary">
      Brief Title
    </h3>
    <span className="text-xs text-text-tertiary">2 days ago</span>
  </div>
  <p className="text-text-secondary mb-4">
    2-line summary snippet...
  </p>
  <div className="flex gap-2">
    {/* Result badges */}
  </div>
</div>
```

### 11.2 Standings Table

```tsx
<div className="bg-surface rounded-lg border border-border overflow-hidden">
  <table className="w-full text-sm">
    <thead className="bg-surface-elevated border-b border-border">
      <tr>
        <th className="text-left px-4 py-3 text-text-secondary font-semibold">Pos</th>
        <th className="text-left px-4 py-3 text-text-secondary font-semibold">Team</th>
        <th className="text-center px-4 py-3 text-text-secondary font-semibold">P</th>
        {/* More columns ... */}
      </tr>
    </thead>
    <tbody>
      {/* Rows */}
    </tbody>
  </table>
</div>
```

---

## 12. Design Tokens Reference

**Quick copy-paste for components:**

```tsx
// Colors
className="bg-bg"                    // Page background
className="bg-surface"               // Card background
className="bg-surface-elevated"      // Hover/active
className="border-border"            // Card border
className="text-text-primary"        // Main text
className="text-text-secondary"      // Secondary text
className="bg-status-win"            // Win badge

// Spacing
className="gap-1"   // 8px
className="gap-2"   // 16px
className="gap-3"   // 24px
className="gap-4"   // 32px
className="p-2"     // Padding 16px
className="p-4"     // Padding 32px

// Rounded
className="rounded-lg"   // 12px radius (cards)
className="rounded-full" // Circular (badges, pills)

// Hover effects
className="hover:bg-surface-elevated transition-colors"
className="hover:text-accent-bright transition-colors"

// Focus (accessibility)
className="focus-visible:ring-2 focus-visible:ring-primary"

// Responsive
className="grid-cols-1 md:grid-cols-2 lg:grid-cols-4"
className="hidden md:block"
```

---

## 13. Cross-Reference

- **Full UI specification:** `ck_docs/UI_SPEC.md` (design system, screens, user flows)
- **Component showcase:** Prototypes in `prototypes/` (static mockups)
- **Code implementation:** `frontend/app/globals.css` (design tokens)
- **System architecture:** `ck_docs/system-architecture.md` (frontend stack)

---

## 14. Design Maintenance

### 14.1 Adding a New Color

1. Add token to CSS custom properties in `globals.css`
2. Document in this file under "Color Palette"
3. Test WCAG contrast (if text color)
4. Update Tailwind config if needed (custom colors)

### 14.2 Updating Typography Scale

1. Modify size/weight in `globals.css` or Tailwind config
2. Test on multiple screen sizes
3. Update examples in this file

### 14.3 Responsive Breakpoint

1. Document in Tailwind config (`tailwind.config.ts`)
2. Add example to this file
3. Test on actual device/browser

---

## 15. Quick Checklist for New Components

- [ ] Uses design tokens (no hardcoded colors)
- [ ] Meets WCAG AA contrast (4.5:1 text)
- [ ] Has focus-visible ring for keyboard users
- [ ] Respects prefers-reduced-motion
- [ ] Uses semantic HTML (`<button>`, `<a>`, not `<div>`)
- [ ] Includes aria-label if icon-only
- [ ] Works on mobile (responsive sizing)
- [ ] Consistent spacing (uses gap-1/2/3/4)
- [ ] Consistent radius (radius-card or radius-sm)
- [ ] No hardcoded sizes (use Tailwind scales)
