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
* Verification mapping: see the status badge table below (ACC-DES-REG-BADGE-STATUS-SPEC, 2026-11-01, binding). It supersedes the older rule that every non-`verified_*` value is UNVERIFIED. Do NOT test for the literal string `verified`.

<a id="status-badges"></a>
**Status badge spec (5 live matrix values, column comment on `jurisdiction_requirements_cited.verification_status`)**

Implement one lookup, `getStatusBadge(status)`, in `components/shared/index.tsx`. It compares statuses case-insensitively after trim. `StatusCell` (RegulatoryTab), `CitationLink` and `RegulatoryChecklist` all use it. A status that is unknown, null or empty falls back to the UNVERIFIED row, so the lookup fails safe. Every badge = Lucide icon (14px, strokeWidth 1.5, `aria-hidden`) + the label word, `text-xs` weight 500, so the status is never conveyed by color alone (WCAG 1.4.1). Tooltip copy goes in `title` AND in an `sr-only` span, so it is not hover-only.

| Status value(s) | Label text | Text/icon token | Lucide icon | Citable? | Tooltip / sr-only copy |
|---|---|---|---|---|---|
| `VERIFIED_STATUTE_TEXT`, `verified_statute_text` | Verified · statute text | `--color-success-text` #007A52 | `CheckCircle2` | Yes | "Quoted or paraphrased from the full text of the cited statute, rule or order." |
| `VERIFIED_OFFICIAL_PAGE`, `verified_url_200` | Verified · official page | `--color-success-text` #007A52 | `CheckCircle2` | Yes | "Official page confirmed live. Content is summarized from the page, not quoted verbatim." |
| `DERIVED_FROM_STATUTE` | Derived from statute | `--color-fg` #1B3139 | `Calculator` | Yes, with the derivation note | "This value was computed from verified statute text and is not stated directly. See the note for the derivation." Render the row's `notes` column (derivation) as the secondary line. |
| `NO_STATE_HOLD_PERIOD` | No state requirement | `--color-muted-fg` #5B6E7D | `MinusCircle` | Yes, as an absence | "The cited statute was read in full and has no hold-period requirement. This is a verified absence, not a gap." Matrix cell value reads "None in cited sections", never blank or "—". |
| `UNVERIFIED`, `unverified_*`, unknown | Unverified | `--color-warning-text` #A3400F | `AlertTriangle` | **No** | "Not yet confirmed against the official text. Do not cite as fact." Keep the `.ll-badge-synthetic` UNVERIFIED chip in `CitationLink`. |
| (no `official_url`) | Flagged gap (no official source) | `--color-warning-text` | `AlertTriangle` | No | Unchanged: `CitationLink` renders "No official source found". |

Contrast ratios (WCAG relative luminance, computed 2026-11-01), shown as bg #F9F7F4 / card #FFFFFF / muted #F0EEEA: success 5.03 / 5.38 / 4.64, fg 12.71 / 13.59 / 11.73, muted-fg 4.95 / 5.29 / 4.56, warning 5.96 / 6.37 / 5.50. All values are at least 4.5:1 for text and at least 3:1 for icons. No new tokens are needed, so the white-label brand layer is unchanged.

Counting rules: add `isCitableStatus(s)`, which is true for the first 4 rows. Use it for `rowVerified`, the KPI and the "gaps only" filter. KPI "Requirements citable" = 85 / 86, with the sub-line "83 verified · 1 derived · 1 no state rule". "Flagged gaps" = UNVERIFIED + no-URL rows = 1 today. Expected rendered badge counts on the live matrix (86 rows): Verified 83 (68 + 15) / Derived 1 (AZ 811_notice_lead_time) / No state requirement 1 (CO scrap_metal_hold_period) / Unverified 1 (CO lead_cable_handling). Keep `isVerifiedStatus` as an alias for strict `verified_*` checks only.

One status signal per row (design review 2026-11-02, binding). `RegulatoryChecklist` renders exactly one status element per item: `<StatusBadge>` when `!isVerifiedStatus(s)`, nothing for strict verified rows. Never print the raw enum (e.g. "(UNVERIFIED)") in UI copy. Pass `hideStatusChip` to `CitationLink` when a `StatusBadge` is already in the same row, so the Unverified state is not shown twice. In `CitationLink`, the secondary-line date prefix is "verified" only when `isCitableStatus(s)`. Otherwise it is "checked", so an Unverified chip never sits next to the word "verified". Use `isVerifiedStatus()` rather than inline `/^verified_/` regexes.

* Chat answers: citations listed under the answer as a "Sources" row (max 5 chips), never inline-only. If retrieval returned only synthetic chunks, replace the answer with: "No official source found for this question."

<a id="ask-insufficient"></a>
**Ask: "not enough to answer" state (ACC-DES-REG-INSUFFICIENT-STATE, 2026-11-02, binding).** This applies when `/api/regulatory/ask` returns `insufficient: true`. That was 15/36 = 41.7% of live answers in eval run a6b4fc05. Retrieval found real official chunks but the model could not answer from them, so the screen must look like a useful partial result, not an error. Implement it as one `AskInsufficient` block in `RegulatoryTab.tsx` AskView. Keep it separate from the other two non-answer modes, `no_real_sources` and `uncited_suppressed`, which keep the one-line NO_SOURCE copy above.

| Part | Rule |
|---|---|
| Container | `rounded-lg border border-border bg-card p-4`, with a 4px left border in `rgb(var(--color-warning-text))` (6.37:1 on card; non-text needs 3:1). Wrap it in `role="status"` inside the existing `aria-live="polite"` region. Add `data-state="insufficient"` so the eval harness and QA can count it. Do not use `text-warning` on body text. |
| Heading | Lucide `SearchX` icon (16px, strokeWidth 1.5, `aria-hidden`) followed by an `h3` `text-sm font-semibold text-foreground`: **"The official sources found don't fully answer this question."** |
| Reason line | Strip the leading `INSUFFICIENT SOURCES:` token on the client (case-insensitive regex `^\s*INSUFFICIENT SOURCES:\s*`). Never show the raw token. Render the rest as `text-sm text-foreground` with the prefix **"What's missing: "** in `font-medium`. If the rest is empty, use "The retrieved passages cover related rules but not the specific point asked." |
| Closest sources | Label `text-xs font-semibold text-secondary`: **"Closest official sources"**. Show at most 3 cards in retrieval order (`res.sources`, not filtered by `cited`). Each card has: (1) a `CitationLink` chip (title ↗, `citation`, `last_verified`, status badge from `getStatusBadge`); (2) a jurisdiction tag (`US` shows as "Federal"); (3) the excerpt as `<blockquote>` `text-sm text-muted-foreground` (5.29:1 on card), border-left 2px `border-border`, clamped to 4 lines with a "Show more" text button (`aria-expanded`). Excerpts are verbatim official text, so never summarize or paraphrase them. Never show a card that has no `url`. |
| Narrow-the-question | Label **"Try a narrower question"**, then up to 3 `button` chips styled like the SUGGESTED chips (44px min height on touch, `focus-visible:ring-2`). Clicking a chip calls `submit()` with: (a) `What does {top source citation} require?` using the first card's `citation`, for example "What does 47 CFR 51.333 require?"; (b) when `jurisdiction_applied` is `ALL` or missing, a chip **"Pick a state above"** that moves focus to the jurisdiction selector and does not submit. The selector lives in the parent RegulatoryTab (L232), so give it `id="reg-jur"` and call `document.getElementById('reg-jur')?.focus()`; (c) the user's question with the top card's jurisdiction name appended, only when (b) is not shown. |
| Disclosure | The last line is `text-xs text-muted-foreground`: "Answers come only from official text. When the text is silent, we show the closest sources instead of guessing. Not legal advice." |
| Never | Never show a generated answer sentence without a citation. Never show the sources list twice (hide the normal "Sources" row in this state). Never mark the result as an error (`EmptyState` is for transport errors only). Never use color alone: the icon and the heading text carry the state. |

All colors are existing tokens (`--color-fg` 13.59:1, `--color-muted-fg` 5.29:1, `--color-warning-text` 6.37:1 on card #FFFFFF), so the white-label BRAND LAYER is unchanged. Copy is independent of the excerpt-size fix tracked under COO-Q-20261101-1846-2 and ACC-ML-REG-POSTTAG-FIXES-1101. When that fix lowers the insufficient rate, the state stays as specified. Acceptance after the tag: `grep -c 'INSUFFICIENT SOURCES' client/src` = 0 in rendered strings (only the strip regex is allowed); `data-state="insufficient"` is present; a known-insufficient question (pick one from app_path_results.csv in run a6b4fc05) shows a heading, 1-3 cards with excerpt + link, and at least 1 narrowing chip; axe reports 0 contrast violations.

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

<a id="kpi-scope-labels"></a>
### §0.4 KPI scope labels: Plan (wave scope) vs Map & Risk (at-risk portfolio). Binding (ACC-DES-PLAN-KPI-LABEL-SPEC, DEC-KPI-CANONICAL-20261102)

**Rule:** a KPI label names exactly one metric definition across the app. If two tabs show the same label, they must show the same value. Map & Risk owns the at-risk portfolio names, which are backed by the governed metric views: **Annual revenue at risk**, **Customers impacted** and **Copper devices**. The Plan tab must never use the words "at risk", "impacted" or "affected" in a label. All labels use sentence case, matching Map. Plan values come from `gold_wave_schedule`. At 2026-11-03 that table has 103 rows, 103 distinct revenue values, a revenue SUM of $53,945,233.08, 255 devices and 35 customers. The fan-out value $1,342.6M must never render under any label.

| Component (current line) | Current label | Required label | Required sub-label (the synthetic qualifier approves ACC-APP-DEF-TILE-SYNTH-LABELS for Plan) | Expected live value |
|---|---|---|---|---|
| `PlanKPIs.tsx:42` | Wire Centers | Wire centers scheduled | `{waves} waves · {states} states · synthetic plan data` | 103 |
| `PlanKPIs.tsx:48` | Copper Devices | Copper devices in scheduled waves | `{critical} critical risk · synthetic plan data` | 255 |
| `PlanKPIs.tsx:54` | Avg Readiness | Avg wave readiness | `{n} fiber-ready · synthetic plan data` | (unchanged) |
| `PlanKPIs.tsx:60` | Crew-Days | Planned crew-days | `{first} → {last} · synthetic plan data` | (unchanged) |
| `PlanKPIs.tsx:66` | Revenue at Risk | Scheduled-wave revenue | `annual · wave plan · synthetic` | $53.9M |
| `PlanKPIs.tsx:72` | Customers Affected | Customers in scheduled waves | `{puc} PUC filings required · synthetic plan data` | 35 |
| `PlanKPIs.tsx:16` `LABELS` (loading/error) | old names | the same 6 required labels, in the same order | `failText(state)` (unchanged) | — |
| `BudgetChart.tsx:87` (Plan › Budget) | Revenue at Risk (Annual) | Scheduled-wave revenue (annual) | — | must equal the KPI tile (both SUM `gold_wave_schedule`) |
| `CostBenefitPanel.tsx:82` (wire-center drawer) | Revenue at Risk (MRR) | Wire-center revenue (MRR, wave plan) | — | per WC |

**Scope note (visible, so it survives screenshots).** When `state === 'live'`, replace the text of the existing `role="note"` line (`PlanKPIs.tsx:120`) with: "Wave-plan scope: wire centers in scheduled retirement waves (synthetic plan data). Map & Risk shows the full at-risk portfolio, so its totals are larger. Excludes footprint revenue on circuits not yet assigned to a wire center." Do not hardcode a dollar figure. Show the unassigned amount only if the API returns it, as "($X.XM)" after "wire center".

**One-line tooltip.** Add an optional `hint?: string` prop to the shared `KpiCard`. This is additive; existing callers do not change. When `hint` is set, render a Lucide `Info` icon (14px, 1.5px stroke, `aria-hidden`) inside a `<button type="button" aria-label="About {label}" aria-describedby={id}>` next to the label. The 24px hit area is padded so the 8px grid holds. The tooltip is `role="tooltip"` with id `{id}`. It shows on hover AND on focus, stays visible while hovered, and closes on Esc (WCAG 1.4.13). Colors: `bg-secondary text-white text-xs`, 13.59:1. The global focus ring comes from tokens.css. Do not use a `title` attribute; it is not keyboard-accessible. Hint text, identical on all 6 Plan tiles: "Wave-plan scope: only wire centers in scheduled retirement waves. Map & Risk shows the full at-risk portfolio."

**Tokens:** no new tokens. Labels and sub-labels use `text-muted-foreground` (#5B6E7D, 5.29:1 on card). Value colors are unchanged.

**Verification (post-deploy, @designer):** `grep -nE "at Risk|Affected|impacted" PlanKPIs.tsx BudgetChart.tsx CostBenefitPanel.tsx` returns 0 label hits. `grep -c "synthetic plan data" PlanKPIs.tsx` returns ≥5. `grep -n "hint" components/shared/index.tsx` shows the prop. /api/plan/kpis `total_revenue_at_risk` is about 53945233. The Plan tile and the Budget label show the same value.

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
