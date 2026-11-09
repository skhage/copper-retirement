/**
 * App.tsx — Copper Retirement Accelerator (unified partner-facing app)
 * DEC-ACCEL-UNIFIED-APP / ACC-APP-UNIFY-SHELL. Evolved in place from retirement-plan.
 *
 * IA (BRAND_GUIDE §0, demo order), URL hash routing:
 *   #map         Map & Risk        <- copper-map           (ACC-APP-PORT-MAP, PORTED 2026-10-25: tabs/map/MapTab.tsx, server/routes/map.js; default route)
 *   #plan[/sub]  Plan              <- retirement-plan      (this app; sub = timeline|table|budget|regulatory|scenarios)
 *   #triage[/sub] Dig Triage        <- dig-triage           (ACC-APP-PORT-TRIAGE, PORTED 2026-10-24: tabs/triage/, server/routes/triage.js)
 *   #regulatory[/sub] Regulatory        <- regulatory-assistant (ACC-APP-PORT-REG, PORTED 2026-10-24: tabs/regulatory/, server/routes/regulatory.js; every answer/row carries source title + official URL)
 *   #commodity   Commodity & Value <- commodity-dashboard  (ACC-APP-PORT-COMMODITY, PORTED 2026-10-25: tabs/commodity/CommodityTab.tsx, server/routes/commodity.js)
 *
 * Sub-tabs (ACC-DES-DEF-SUBTAB-HASH-1108): #plan/<timeline|table|budget|regulatory|scenarios>,
 *   #triage/<map|table|log>, #regulatory/<matrix|ask|sources>; unknown sub -> default. Tab/sub changes
 *   pushState so browser Back restores the prior tab/sub-tab.
 *
 * Styling: styles/tokens.css only (ACC-APP-TOKENS-WIRE). Partner rebrand = edit the BRAND LAYER there.
 */
import { useState, useEffect, useCallback } from 'react';
import { LakeLinkHeader, TabBar, ErrorBoundary, panelId, tabId } from './components/shared';
import { PlanTab, isPlanSub, type PlanSub } from './tabs/PlanTab';
import { TriageTab, isTriageSub, type TriageSub } from './tabs/triage/App';
import { RegulatoryTab, isRegSub, type RegSub } from './tabs/regulatory/RegulatoryTab';
import { MapTab } from './tabs/map/MapTab';
import { CommodityTab } from './tabs/commodity/CommodityTab';
import { USE_MOCK_DATA } from './mock/mockData';

export interface PlanFilters {
  wave: string;       // 'all' | '1' | '2' | ... | '8'
  state: string;      // 'all' | 'CO' | 'MN' | ...
  status: string;     // 'all' | 'planned' | 'in_progress' | ...
  constraint: string; // 'all' | 'contract_locked' | 'regulatory_notice_pending' | ...
}

// BRAND_GUIDE §0.3 (ACC-DES-DEF-SHELL-SYNTH-LABELS): ONE header badge. Every tab except Regulatory has synthetic
// panels, so the app-level source is MIXED. MOCK only when bundled mock data is on.
const DATA_SOURCE = USE_MOCK_DATA ? 'MOCK' : 'MIXED';
// Release shown in the footer (package.json version is a 0.0.0 placeholder).
// ACC-DES-DEF-FOOTER-VERSION-1107: sourced from build config, not a literal. vite.config.ts injects
// __APP_RELEASE__ from env APP_RELEASE at `npm run build` (app.yaml / bundle config env); default 'dev'.
declare const __APP_RELEASE__: string | undefined;
const APP_VERSION = typeof __APP_RELEASE__ === 'string' && __APP_RELEASE__ ? __APP_RELEASE__ : 'dev';
const SYNTHETIC_DISCLOSURE = 'Synthetic data disclosure: network, customer, plant and incident data are generated for demonstration and do not represent any real carrier. Regulatory content links to official public sources.';

const TOP_TABS = [
  { id: 'map', label: 'Map & Risk' },
  { id: 'plan', label: 'Plan' },
  { id: 'triage', label: 'Dig Triage' },
  { id: 'regulatory', label: 'Regulatory' },
  { id: 'commodity', label: 'Commodity & Value' },
] as const;
type TopTab = (typeof TOP_TABS)[number]['id'];

interface Route { tab: TopTab; planSub: PlanSub; triageSub: TriageSub; regSub: RegSub }

// Demo order: land on Map & Risk (ACC-APP-PORT-MAP landed 2026-10-25).
const DEFAULT_ROUTE: Route = { tab: 'map', planSub: 'timeline', triageSub: 'map', regSub: 'matrix' };

function parseHash(hash: string): Route {
  const [tab, sub] = hash.replace(/^#\/?/, '').split('/');
  const top = TOP_TABS.find((t) => t.id === tab)?.id ?? DEFAULT_ROUTE.tab;
  // A sub only applies to its own top tab; other tabs keep their defaults.
  return {
    tab: top,
    planSub: top === 'plan' && isPlanSub(sub) ? sub : DEFAULT_ROUTE.planSub,
    triageSub: top === 'triage' && isTriageSub(sub) ? sub : DEFAULT_ROUTE.triageSub,
    regSub: top === 'regulatory' && isRegSub(sub) ? sub : DEFAULT_ROUTE.regSub,
  };
}

function toHash(r: Route) {
  if (r.tab === 'plan') return `#plan/${r.planSub}`;
  if (r.tab === 'triage') return `#triage/${r.triageSub}`;
  if (r.tab === 'regulatory') return `#regulatory/${r.regSub}`;
  return `#${r.tab}`;
}

export default function App() {
  const [route, setRoute] = useState<Route>(() => parseHash(window.location.hash));

  useEffect(() => {
    const onHash = () => setRoute(parseHash(window.location.hash));
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const navigate = useCallback((next: Route) => {
    const h = toHash(next);
    // pushState (not replaceState) so Back restores the prior tab/sub-tab; Back fires hashchange -> parseHash.
    if (window.location.hash !== h) window.history.pushState(null, '', h);
    setRoute(next);
  }, []);

  const label = TOP_TABS.find((t) => t.id === route.tab)!.label;

  return (
    <div className="min-h-screen bg-background font-sans">
      <LakeLinkHeader
        subtitle="Copper Retirement Accelerator"
        tagline="Find the copper, plan the path, dig safely, stay compliant, monetize the scrap"
        dataSource={DATA_SOURCE}
      />

      <TabBar
        tabs={TOP_TABS}
        activeId={route.tab}
        onChange={(tab) => navigate({ ...route, tab })}
        idPrefix="top"
        ariaLabel="Accelerator sections"
      />

      <main
        role="tabpanel"
        id={panelId('top', route.tab)}
        aria-labelledby={tabId('top', route.tab)}
        className="px-4 md:px-6 py-4"
      >
        <ErrorBoundary name={label} key={route.tab}>
          {route.tab === 'map' && <MapTab />}
          {route.tab === 'plan' && (
            <PlanTab sub={route.planSub} onSubChange={(planSub) => navigate({ ...route, tab: 'plan', planSub })} />
          )}
          {route.tab === 'triage' && (
            <TriageTab sub={route.triageSub} onSubChange={(triageSub) => navigate({ ...route, tab: 'triage', triageSub })} />
          )}
          {route.tab === 'regulatory' && (
            <RegulatoryTab sub={route.regSub} onSubChange={(regSub) => navigate({ ...route, tab: 'regulatory', regSub })} />
          )}
          {route.tab === 'commodity' && <CommodityTab />}
        </ErrorBoundary>
      </main>

      <footer className="border-t border-border px-4 md:px-6 py-3 text-xs text-muted-foreground" data-testid="synthetic-disclosure">
        <p className="m-0">{SYNTHETIC_DISCLOSURE}</p>
        <p className="m-0 mt-1">Version {APP_VERSION}</p>
      </footer>
    </div>
  );
}
