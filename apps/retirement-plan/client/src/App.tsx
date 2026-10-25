/**
 * App.tsx — Copper Retirement Accelerator (unified partner-facing app)
 * DEC-ACCEL-UNIFIED-APP / ACC-APP-UNIFY-SHELL. Evolved in place from retirement-plan.
 *
 * IA (BRAND_GUIDE §0, demo order), URL hash routing:
 *   #map         Map & Risk        <- copper-map           (ACC-APP-PORT-MAP, PORTED 2026-10-25: tabs/map/MapTab.tsx, server/routes/map.js; default route)
 *   #plan[/sub]  Plan              <- retirement-plan      (this app; sub = timeline|table|budget|regulatory|scenarios)
 *   #triage      Dig Triage        <- dig-triage           (ACC-APP-PORT-TRIAGE, PORTED 2026-10-24: tabs/triage/, server/routes/triage.js)
 *   #regulatory  Regulatory        <- regulatory-assistant (ACC-APP-PORT-REG, PORTED 2026-10-24: tabs/regulatory/, server/routes/regulatory.js; every answer/row carries source title + official URL)
 *   #commodity   Commodity & Value <- commodity-dashboard  (ACC-APP-PORT-COMMODITY, PORTED 2026-10-25: tabs/commodity/CommodityTab.tsx, server/routes/commodity.js)
 *
 * Styling: styles/tokens.css only (ACC-APP-TOKENS-WIRE). Partner rebrand = edit the BRAND LAYER there.
 */
import { useState, useEffect, useCallback } from 'react';
import { LakeLinkHeader, TabBar, ErrorBoundary, panelId, tabId } from './components/shared';
import { PlanTab, isPlanSub, type PlanSub } from './tabs/PlanTab';
import { TriageTab } from './tabs/triage/App';
import { RegulatoryTab } from './tabs/regulatory/RegulatoryTab';
import { MapTab } from './tabs/map/MapTab';
import { CommodityTab } from './tabs/commodity/CommodityTab';

export interface PlanFilters {
  wave: string;       // 'all' | '1' | '2' | ... | '8'
  state: string;      // 'all' | 'CO' | 'MN' | ...
  status: string;     // 'all' | 'planned' | 'in_progress' | ...
  constraint: string; // 'all' | 'contract_locked' | 'regulatory_notice_pending' | ...
}

const TOP_TABS = [
  { id: 'map', label: 'Map & Risk' },
  { id: 'plan', label: 'Plan' },
  { id: 'triage', label: 'Dig Triage' },
  { id: 'regulatory', label: 'Regulatory' },
  { id: 'commodity', label: 'Commodity & Value' },
] as const;
type TopTab = (typeof TOP_TABS)[number]['id'];

interface Route { tab: TopTab; planSub: PlanSub }

// Demo order: land on Map & Risk (ACC-APP-PORT-MAP landed 2026-10-25).
const DEFAULT_ROUTE: Route = { tab: 'map', planSub: 'timeline' };

function parseHash(hash: string): Route {
  const [tab, sub] = hash.replace(/^#\/?/, '').split('/');
  const top = TOP_TABS.find((t) => t.id === tab)?.id ?? DEFAULT_ROUTE.tab;
  return { tab: top, planSub: isPlanSub(sub) ? sub : DEFAULT_ROUTE.planSub };
}

function toHash(r: Route) { return r.tab === 'plan' ? `#plan/${r.planSub}` : `#${r.tab}`; }

export default function App() {
  const [route, setRoute] = useState<Route>(() => parseHash(window.location.hash));

  useEffect(() => {
    const onHash = () => setRoute(parseHash(window.location.hash));
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const navigate = useCallback((next: Route) => {
    const h = toHash(next);
    if (window.location.hash !== h) window.history.replaceState(null, '', h);
    setRoute(next);
  }, []);

  const label = TOP_TABS.find((t) => t.id === route.tab)!.label;

  return (
    <div className="min-h-screen bg-background font-sans">
      <LakeLinkHeader
        subtitle="Copper Retirement Accelerator"
        tagline="Find the copper, plan the path, dig safely, stay compliant, monetize the scrap"
        dataSource="MOCK"
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
            <PlanTab sub={route.planSub} onSubChange={(planSub) => navigate({ tab: 'plan', planSub })} />
          )}
          {route.tab === 'triage' && <TriageTab />}
          {route.tab === 'regulatory' && <RegulatoryTab />}
          {route.tab === 'commodity' && <CommodityTab />}
        </ErrorBoundary>
      </main>
    </div>
  );
}
