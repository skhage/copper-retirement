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

<a id="demo-click-path"></a>
### §0.1 R2 Demo Click-Path (presenter script, ~12 min) — ACC-DES-DEMO-CLICKPATH

Linked from PARTNER-PLAYBOOK §5 via `apps/BRAND_GUIDE.md#demo-click-path`. Tab order = sales narrative; never skip back. Each step: **click → say → proof on screen**.

| Step | Tab / route | Click | Talk track (one line) | Proof on screen | Data label |
|---|---|---|---|---|---|
| 0 | Header | Land on `#map` (default) | "One accelerator, five questions a copper program has to answer." | Header badge shows MIXED; footer disclosure visible | MIXED |
| 1 | Map & Risk `#map` | KPI row → click highest-risk wire center hex → device drawer opens | "Where is the copper and what is at risk." | Risk score from serving endpoint `copper-retirement-risk`; drawer shows device + alarms | SYNTHETIC badge on map title (TMF network data is synthetic) |
| 2 | Plan `#plan/timeline` → `#plan/budget` → `#plan/scenarios` | Select wave → Budget sub-tab → compare 2 scenarios | "Capital-efficient path to zero copper, wave by wave." | Gantt + budget vs. salvage; scenario delta KPI | SYNTHETIC on plan panels |
| 3 | Dig Triage `#triage` | Click newest incident → detail drawer → ask triage agent one question | "When a dig damages plant, triage takes seconds, not hours." | 811 ticket fields from `stg_811_dig_ticket`; agent answer with cited locate rule | SYNTHETIC on incident panels; citations use CitationLink |
| 4 | Regulatory `#regulatory` | Jurisdiction matrix → pick state → FCC workflow stepper → open one citation | "Every requirement links to the official source — no invented rules." | Rows from `copper_retirement.jurisdiction_requirements_cited` + `regulatory_source_register` (`official_url` on every row); link opens fcc.gov / ecfr.gov in new tab | LIVE (real sources). Free-text RAG hidden or labeled "synthetic, not citable" until ACC-REG-VS-RESYNC |
| 5 | Commodity & Value `#commodity` | Move ROI slider low → base → high | "Here is what the copper is worth and the payback the SOW funds." | Metric view `copper_retirement.copper_partner_value` + `roi_calculator_assumptions`; price as-of date + source next to the price KPI | MIXED: price source labeled; plant volumes SYNTHETIC |
| 6 | Close | Back to header | "Partner rebrand = one token file; deploy = one DAB command." | — | — |

**Presenter rules:** keep browser at ≥1280px (drawers render right-side); if a tab errors, the ErrorBoundary Retry keeps chrome — click Retry once, then move on (do not reload the app mid-demo). Never claim a synthetic number is a customer number.

<a id="citation-pattern"></a>
### §0.2 Regulatory citation display pattern (binding)

* Every regulatory fact (matrix cell, stepper step, chat answer sentence group) ends with one or more `CitationLink` chips: `{title} ↗` in `text-primary-strong` underlined, `text-xs`, new tab, `rel="noopener noreferrer"`, sr-only "(opens official source in new tab)".
* Chip text = `regulatory_source_register.title`; tooltip/secondary line = `citation` (e.g. "47 CFR 51.325") + `last_verified` date. Never render a fact without an `official_url`; if missing, render the EmptyState "Source not yet verified" and do not show the fact.
* Verification mapping (matches real register values): `verified_url_200` and `verified_statute_text` = verified (no badge); any other value (e.g. `unverified_detail`) = UNVERIFIED badge. Do NOT test for the literal string `verified`.
* Chat answers: citations listed under the answer as a "Sources" row (max 5 chips), never inline-only. If retrieval returned only synthetic chunks, replace the answer with: "No official source found for this question."

<a id="synthetic-banner"></a>
### §0.3 Synthetic-data labeling spec (charter rule: synthetic must be labeled in the UI)

| Surface | Component | Rule |
|---|---|---|
| Header data badge | `LakeLinkHeader` badge | `LIVE` (all panels real) / `SYNTHETIC` (all synthetic) / `MIXED` (any synthetic). Uses `.ll-badge-synthetic` for SYNTHETIC/MIXED; text never color-only (always the word). |
| Panel title | `SyntheticBadge` | Rendered next to every panel title (`TabHeader badges`) whose source table comment / `is_synthetic` = true. |
| Tab-level banner | one-line strip under `TabHeader` | Shown on any tab where ALL panels are synthetic: Info icon (Lucide 16px, 1.5px) + "Demo data: network, customer and plant records on this tab are synthetic. Regulatory sources are real and linked." `bg-muted text-foreground text-sm`, border-left 4px `rgb(var(--color-warning-text))`; not dismissible during demo. |
| Footer | app footer | Persistent: "Synthetic data disclosure: network, customer, plant and incident data are generated for demonstration and do not represent any real carrier. Regulatory content links to official public sources." + app version. |
| Exports / screenshots | CSV/PNG export | Append "SYNTHETIC" to filename and a footer line in the image. |

Colors come from tokens only (`--color-synthetic-bg` / `--color-synthetic-fg`, AA ≥4.5:1). Do not use Tailwind `yellow-*` utilities.

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
* Use `.ll-badge-synthetic` / `SyntheticBadge` from tokens.css (SUPERSEDES the old `bg-yellow-100 text-yellow-800` utilities). Spec: §0.3.

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
