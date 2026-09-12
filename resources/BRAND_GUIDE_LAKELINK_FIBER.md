# Lakelink Fiber — Brand Guide

**Version:** 1.0 | **Author:** @designer | **Date:** 2026-09-12
**Authority:** This is the binding brand reference for all Copper Retirement demo apps.
@app-developer must follow these specs. Deviations require @designer approval.

---

## 1. Brand Identity

**Name:** Lakelink Fiber
**Wordmark:** "Lakelink Fiber" — text only, no icon/logo. Always left-aligned in the app nav header.
**Tone:** Professional, technical, trustworthy. No jargon in user-facing labels.
Abbreviations spelled out on first use.

---

## 2. Color Palette

### Primary
| Token | Hex | Usage |
|---|---|---|
| `--ll-primary` | `#FF3621` | Primary actions, active tab indicators, critical risk tier |
| `--ll-secondary` | `#1B3139` | Nav background, card headers, body text on light |
| `--ll-accent` | `#00A972` | Success states, positive indicators, compliance-clear |

### Surface & Background
| Token | Hex | Usage |
|---|---|---|
| `--ll-surface` | `#F9F7F4` | Page background, card surface |
| `--ll-surface-elevated` | `#FFFFFF` | Cards, modals, popovers |
| `--ll-surface-dark` | `#1B3139` | Dark-mode sections, map background |

### Text
| Token | Hex | Usage |
|---|---|---|
| `--ll-text-primary` | `#1B3139` | Body text on light backgrounds |
| `--ll-text-secondary` | `#6E8898` | Captions, labels, muted text |
| `--ll-text-inverse` | `#FFFFFF` | Text on dark backgrounds |

### Semantic (Status)
| Token | Hex | Usage |
|---|---|---|
| `--ll-critical` | `#FF3621` | Critical risk, overdue items |
| `--ll-high` | `#FF8C69` | High risk |
| `--ll-medium` | `#FFD700` | Medium risk, warnings |
| `--ll-low` | `#00A972` | Low risk, success |
| `--ll-info` | `#60A5FA` | Informational, neutral highlights |

### Data Visualization (sequential palette)
Use in this order for multi-series charts:
1. `#FF3621` (Primary Red)
2. `#1B3139` (Dark Navy)
3. `#00A972` (Green)
4. `#6E8898` (Slate)
5. `#FF8C69` (Coral)
6. `#FFD700` (Gold) — extend only if >5 series

**FORBIDDEN colors:**
- `#EB1600` (too close to error red — use `#FF3621`)
- `#40D1F5` (off-brand cyan — use `#60A5FA`)
- Slate theme defaults (`#0f172a`, `#1e293b`, `#334155`) — replace with brand tokens

---

## 3. Typography

| Element | Font | Weight | Size |
|---|---|---|---|
| Page title | Inter / system sans-serif | 700 (Bold) | 24px / 1.5rem |
| Section header | Inter / system sans-serif | 600 (Semibold) | 18px / 1.125rem |
| KPI value | Inter / system sans-serif | 700 (Bold) | 28px / 1.75rem |
| KPI label | Inter / system sans-serif | 400 (Regular) | 12px / 0.75rem, UPPERCASE, tracking 0.05em |
| Body text | Inter / system sans-serif | 400 (Regular) | 14px / 0.875rem |
| Table header | Inter / system sans-serif | 600 (Semibold) | 13px / 0.8125rem |
| Table cell | Inter / system sans-serif | 400 (Regular) | 13px / 0.8125rem |
| Data values | JetBrains Mono / monospace | 500 (Medium) | 13px / 0.8125rem |
| Caption/muted | Inter / system sans-serif | 400 (Regular) | 11px / 0.6875rem |

---

## 4. Icons

- **Library:** Lucide React (`lucide-react`)
- **Stroke weight:** 1.5px (consistent across all icons)
- **Size:** 16px in body context, 20px in nav, 24px in KPI cards
- **Color:** Inherits from text color (never hardcoded)
- **NO mixing** icon families (no FontAwesome, no Material, no Heroicons alongside Lucide)

---

## 5. Spacing & Layout

- **Grid:** 8px base unit
- **Card padding:** 16px (2 units)
- **Section gap:** 24px (3 units)
- **KPI card grid:** Use `grid-cols-5` for 5 or fewer KPIs, `grid-cols-6` for 6
  - Both apps MUST use the same card component and layout density
- **Page margin:** 24px horizontal on desktop, 16px on mobile
- **Border radius:** 8px on cards, 4px on buttons/inputs

---

## 6. Component Patterns (Cross-App Consistency)

These components MUST look and behave identically across all 5 apps:

### Nav Header
- Left: "Lakelink Fiber" wordmark (text, `--ll-secondary`, 600 weight, 16px)
- Left: App subtitle (muted, 13px)
- Right: Data source badge (LIVE/MOCK + SYNTHETIC)
- Background: `--ll-surface` with bottom border `#E5E2DD`

### KPI Card
- Background: `--ll-surface-elevated`
- Label: uppercase, tracking-wide, `--ll-text-secondary`, 12px
- Value: `--ll-text-primary` or semantic color, 28px bold
- Subtitle: `--ll-text-secondary`, 11px
- Border: 1px `#E5E2DD`
- No drop shadows

### Data Table
- Header: `--ll-surface`, `--ll-text-secondary`, 600 weight
- Rows: alternating `--ll-surface-elevated` / `--ll-surface`
- Conditional formatting: use semantic status colors only
- Sortable columns indicated with Lucide `ArrowUpDown` icon

### Filter Panel
- Labels: `--ll-text-secondary`, 12px, uppercase
- Dropdowns: native `<select>` or AppKit Select with `--ll-surface-elevated` background
- Clear button on each filter

---

## 7. Accessibility (WCAG 2.1 AA)

- **Color contrast:** 4.5:1 for normal text, 3:1 for large text (18px+ bold or 24px+ regular)
- **Focus indicators:** Visible focus ring (`outline: 2px solid #FF3621, offset 2px`) on all interactive elements
- **Keyboard navigation:** All interactive elements reachable via Tab, Escape closes modals/sidebars
- **Screen reader labels:** `aria-label` on icon-only buttons, `role="status"` on KPI values
- **Color-blind safe:** Never convey information through color alone — pair with icons, text, or patterns

---

## 8. Data Visualization

- **Axes:** Always labeled with units (e.g., "Devices", "Risk Score (0-100)")
- **No 3D charts** ever
- **Tooltips:** `--ll-surface-dark` background, `--ll-text-inverse`, 13px, 8px padding, 4px radius
- **Map tiles:** US scope, `--ll-surface-dark` for land, `--ll-secondary` for water
- **Bubble charts:** Size legend required when bubble size encodes data
- **Color ramps:** Use the sequential palette in section 2, never raw Tailwind utilities

---

## 9. App-Specific Notes

### copper-map (Beat 1)
- Uses Dash (Python) for the primary `app.py` AND AppKit (React/TS) for `client/`
- **Both must converge** to the same brand — the Dash version currently uses Slate theme
- Map risk tiers: critical/high/medium/low map to `--ll-critical`/`--ll-high`/`--ll-medium`/`--ll-low`

### regulatory-assistant (Beat 4)
- Uses AppKit (React/TS)
- Citation sidebar: `--ll-surface-elevated` background, highlighted passage in `#FFF3CD` (warm yellow)
- Compliance status: green=clear, yellow=pending, red=blocked — use semantic tokens

### dig-triage, retirement-plan, commodity-dashboard (Beats 3/2/5)
- Deferred but scaffolds should pre-comply with this guide

---

## 10. Anti-Patterns (DO NOT)

- Do NOT use Slate/Tailwind default dark theme (`bg-slate-900`, `#0f172a`) as primary surface
- Do NOT hardcode hex colors inline — use CSS custom properties or Tailwind theme extension
- Do NOT use `dbc.themes.SLATE` in Dash — create a custom Lakelink theme or use `dbc.themes.FLATLY` as base
- Do NOT show CA, TX, FL, NY in mock data — use LEGACY_STATES: CO, MN, WA, OR, ID, AZ
- Do NOT abbreviate without context ("PP" → "Patch Panel" first, then abbrev)
- Do NOT omit loading skeletons or error states
