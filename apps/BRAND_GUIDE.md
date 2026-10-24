# Lakelink Fiber — Brand Guide

> Canonical design reference for the Copper Retirement Accelerator (2 apps: unified accelerator app `apps/retirement-plan` + internal `copper-task-board`).
> Last updated: 2026-10-24 (ACC-APP-IA, @designer — binding).
>
> **Single source of truth for tokens:** `apps/retirement-plan/client/src/styles/tokens.css`. Where this guide and tokens.css disagree, **tokens.css wins**. Partner white-label = edit only the BRAND LAYER block in tokens.css. Do NOT hardcode hex values in components or in `tailwind.config` — map Tailwind keys to the CSS variables (snippet at the bottom of tokens.css). Retiring apps (commodity-dashboard, copper-map, dig-triage, regulatory-assistant) receive no further brand fixes.

---

## §0 Information Architecture — Unified Accelerator App (ACC-APP-IA)

**Shell (top → bottom):** `LakeLinkHeader` (brand wordmark from `--brand-name`, product title "Copper Retirement Accelerator", data badge LIVE / SYNTHETIC / MIXED) → top-level tab bar (`.ll-tabs`, `role="tablist"`) → tab panel (`role="tabpanel"`, `aria-labelledby`) → footer (data-source disclosure + synthetic-data notice + version).

**Top-level tabs (fixed order = sales narrative / demo script):**

| # | Tab label | Hash route | Question it answers | Primary content | Source app |
|---|-----------|------------|---------------------|-----------------|------------|
| 1 | Map & Risk | `#map` | Where is the copper and what is at risk? | KPI row, hex/wire-center risk map, filter panel, device drawer, what-if | copper-map |
| 2 | Plan | `#plan` | What is the capital-efficient path to zero copper? | Sub-tabs: Timeline, Migration Table, Budget, Wave Checklist, Scenarios | retirement-plan (host) |
| 3 | Dig Triage | `#triage` | What happens when a dig damages plant? | KPI row, incident map + table, detail drawer, triage agent chat | dig-triage |
| 4 | Regulatory | `#regulatory` | Are we clear on regulations? | Cited Q&A chat, jurisdiction matrix, FCC workflow stepper, source register | regulatory-assistant |
| 5 | Commodity & Value | `#commodity` | What is the copper worth and what is the ROI? | Partner value KPIs (lbs, $ at LME/IMF, opex, customers migrated), price chart, sell/hold, recovery tracker | commodity-dashboard |

**Rules (binding for @app-developer):**
* Max 2 nav levels: top tabs + optional sub-tabs (Plan only). Sub-tabs use the same `.ll-tab` styling at `text-sm`; no pills, no sidebars.
* Deep-linkable: hash route per tab and per Plan sub-tab (`#plan/timeline`); browser back works; default `#map`.
* Every tab follows one page template: (1) tab title H1 24px/700 + one-line question subtitle in `muted-foreground`; (2) KPI row `grid-cols-2 sm:grid-cols-3 lg:grid-cols-6`, `gap-3`; (3) primary viz; (4) detail drawer/panel on selection (right drawer ≥lg, bottom sheet <lg).
* Tab bar scrolls horizontally <640px (no wrapping, no hamburger); 44px min touch target.
* Keyboard: arrow keys move between tabs (WAI-ARIA tabs pattern), `Tab` enters panel, visible focus ring everywhere (global rule in tokens.css).
* Every regulatory fact renders source title + official URL (`CitationLink` shared component, opens new tab, `rel="noopener"`); unverified rows show an UNVERIFIED badge.
* Any panel backed by synthetic data shows `.ll-badge-synthetic` “SYNTHETIC” next to its title; header badge = MIXED while any tab is synthetic.
* Shared components live once in `client/src/components/shared/`: LakeLinkHeader, TabBar, KpiCard, SyntheticBadge, CitationLink, EmptyState, ErrorBoundary.
* Empty/error states: never a blank panel. EmptyState = icon + one sentence + what to do; errors keep the tab chrome and show retry.
* Inter must actually load: add `<link rel="preconnect" href="https://fonts.googleapis.com">` + Inter 400/500/600/700 stylesheet in `client/index.html` (or self-host for air-gapped partner deploys).

**copper-task-board** (internal ops app) consumes the same token names in `static/index.html` `:root` (copy the BRAND LAYER + NEUTRALS blocks; rename `--aubergine` → `--color-secondary`; `--muted` → `--color-muted-fg` #5B6E7D). See ACC-LEGACY-TASKBOARD-WCAG.

---

## §1 Color Palette

| Token               | Hex       | Tailwind Key           | Usage                                |
| ------------------- | --------- | ---------------------- | ------------------------------------ |
| Primary             | `#FF3621` | `primary`              | CTAs, active states, alerts, accent  |
| Secondary / Navy    | `#1B3139` | `secondary`, `navy`    | Text headings, dark surfaces         |
| Accent / Green      | `#00A972` | `accent`               | Success, positive metrics, confirm   |
| Surface             | `#F9F7F4` | `background`           | Page background                      |
| Surface Elevated    | `#FFFFFF` | `card`                 | Cards, panels, modals                |
| Text Primary        | `#1B3139` | `foreground`           | Body text, headings                  |
| Text Secondary      | `#5B6E7D` | `muted.foreground`     | Labels, subtitles, captions (SETTLED 2026-10-24; #6E8898 is NOT a text color) |
| Primary Strong      | `#C8200C` | `primary.strong`       | Red text, primary button bg (white text 5.73:1) |
| Accent Strong       | `#007A52` | `accent.strong`        | Green / success text (5.03:1)        |
| Warning Text        | `#A3400F` | `warning`              | Warning text (replaces salmon text)  |
| Input Border        | `#7A8B98` | `input`                | Form controls, meaningful borders (≥3:1) |
| Border              | `#E5E2DD` | `border`               | Card borders, dividers               |
| Muted Background    | `#F0EEEA` | `muted`                | Hover states, secondary surfaces     |
| Salmon              | `#FF8C69` | —                      | Data viz secondary, warnings         |
| Steel               | `#6E8898` | —                      | Data viz tertiary (large text only on light bg) |

### Data Visualization Sequence
`#FF3621` → `#1B3139` → `#00A972` → `#6E8898` → `#FF8C69`

### Risk / Severity Colors
| Level    | Color     |
| -------- | --------- |
| Critical | `#FF3621` |
| High     | `#FF8C69` (fill only; label text in `foreground` or `warning`) |
| Medium   | `#6E8898` |
| Low      | `#00A972` |

---

## §2 Canonical Tailwind Config

All React apps MUST use this exact Tailwind configuration in `client/index.html`:

```js
tailwind.config = {
  theme: {
    extend: {
      colors: {
        background: '#F9F7F4',
        foreground: '#1B3139',
        primary: { DEFAULT: '#FF3621', foreground: '#FFFFFF' },
        secondary: { DEFAULT: '#1B3139', foreground: '#FFFFFF' },
        accent: { DEFAULT: '#00A972', foreground: '#FFFFFF' },
        muted: { DEFAULT: '#F0EEEA', foreground: '#5B6E7D' }, // SUPERSEDED: use the var()-based mapping in client/src/styles/tokens.css
        border: '#E5E2DD',
        card: { DEFAULT: '#FFFFFF', foreground: '#1B3139' },
      },
    },
  },
};
```

`<body>` MUST include `class="bg-background text-foreground"`.

---

## §3 Typography

| Property       | Value                              |
| -------------- | ---------------------------------- |
| Font Family    | `Inter, system-ui, sans-serif`     |
| Heading Weight | 700 (bold)                         |
| Body Weight    | 400 (regular)                      |
| Label Weight   | 500 (medium)                       |
| Base Size      | 14–15px                            |
| Line Height    | 1.4–1.5                            |
| Icons          | Lucide, 1.5px stroke               |

---

## §4 Spacing & Layout

* Grid unit: **8px**
* Card border-radius: **8px**
* Card padding: **12px** (compact) / **16px** (standard)
* Page padding: **16px** (mobile) / **24px** (desktop)
* KPI grid: responsive — `grid-cols-2 sm:grid-cols-3 lg:grid-cols-6`
* Gap: **12px** (`gap-3`)
* Accessibility: **WCAG 2.1 AA** minimum

---

## §5 Component Patterns

### Nav Header (LakeLinkHeader)
All apps use `LakeLinkHeader.tsx` — a shared component with:
* Background: `#F9F7F4` (surface) with `1px solid #E5E2DD` bottom border
* Left: "Lakelink Fiber" wordmark (16px, 600 weight, `#1B3139`) + app subtitle (24px, 700 weight) + optional tagline
* Right: data source badge (LIVE/MOCK) + optional children (filters)
* Font: Inter

### Tab Navigation
* Underline (border-bottom) active indicator using `border-primary text-foreground font-semibold`
* Inactive: `border-transparent text-muted-foreground hover:text-foreground`
* Focus ring: `focus-visible:ring-2 focus-visible:ring-[#FF3621]`
* NO filled/pill tab backgrounds
* **WCAG note:** `text-primary` (#FF3621) on surface (#F9F7F4) is 3.39:1 — FAILS AA for normal text. Use `text-foreground` (#1B3139) for tab labels (12.71:1). The red underline accent provides visual tab identity.

### KPI Cards
* Container: `bg-card rounded-lg border p-3 shadow-sm`
* Label: `text-xs text-muted-foreground` (uppercase optional)
* Value: `text-xl font-bold` with semantic color
* Subtext: `text-xs text-muted-foreground mt-1`

### Buttons
* Primary: `bg-primary-strong text-primary-foreground rounded-md hover:bg-primary-strong/90` (white on #FF3621 is 3.62:1 and FAILS AA for 14px text)
* Focus: `focus-visible:ring-2 focus-visible:ring-[#FF3621] focus-visible:ring-offset-2`

### Data Badge (Synthetic)
* `text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded`

---

## §6 Python/Dash Apps

Dash apps (copper-map) define brand constants as Python variables:

```python
LL_PRIMARY = "#FF3621"
LL_SECONDARY = "#1B3139"
LL_ACCENT = "#00A972"
LL_SURFACE = "#F9F7F4"
LL_SURFACE_ELEVATED = "#FFFFFF"
LL_TEXT_PRIMARY = "#1B3139"
LL_TEXT_SECONDARY = "#5B6E7D"
LL_BORDER = "#E5E2DD"
```

---

## §7 Anti-Patterns (DO NOT USE)

* ❌ Aubergine/purple sidebars (`#3f0e40`) — this is Slack, not Lakelink
* ❌ `#d4571f` for copper — use `#FF3621` (Databricks Red)
* ❌ System font stacks without Inter
* ❌ Filled/pill tab backgrounds — use underline active indicator
* ❌ Different border colors across apps (`#D9D4CF` vs `#E5E2DD`)
* ❌ `box-shadow` on KPI cards when the design calls for `border` only
* ❌ Inline styles for standard patterns — use Tailwind utilities
* ❌ Primary `#FF3621` or Accent `#00A972` for normal-sized text on light backgrounds — AA-compliant only for large text (≥18px bold / ≥24px normal)
* ❌ Salmon `#FF8C69` as foreground text on light backgrounds — fails even large-text AA (2.28:1 on white)
