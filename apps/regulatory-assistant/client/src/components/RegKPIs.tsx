/**
 * RegKPIs.tsx
 * Top bar KPI cards for the Regulatory Assistant.
 * Fetches live KPIs from the fcc_regulatory_document corpus.
 * Falls back to mock KPIs if the API is unavailable.
 *
 * Follows BRAND_GUIDE §6 KPI Card spec:
 *   - Background: --ll-surface-elevated (#FFFFFF)
 *   - Label: uppercase, tracking-wide, --ll-text-secondary (#6E8898), 12px
 *   - Value: --ll-text-primary (#1B3139) or semantic color, 28px bold
 *   - Subtitle: --ll-text-secondary, 11px (optional)
 *   - Border: 1px #E5E2DD, radius 8px, no shadows
 */
import { useState, useEffect } from 'react';
import { fetchKPIs } from '../api/corpus';
import { getMockKPIs } from '../mock/mockData';

/* Lakelink Fiber semantic status colors (BRAND_GUIDE §2) */
const LL_TEXT_PRIMARY   = '#1B3139';
const LL_TEXT_SECONDARY = '#6E8898';
const LL_BORDER = '#E5E2DD';
const LL_ACCENT = '#00A972';

interface RegKPIsProps {
  jurisdictionFilter: string;
}

interface KPICard {
  label: string;
  value: string | number;
  color: string;
  sub?: string;
}

function KPISkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          style={{
            background: '#FFFFFF',
            border: `1px solid ${LL_BORDER}`,
            borderRadius: 8,
            padding: 12,
          }}
        >
          <div
            className="animate-pulse rounded"
            style={{ height: 12, width: '60%', backgroundColor: 'rgba(27,49,57,0.08)', marginBottom: 8 }}
          />
          <div
            className="animate-pulse rounded"
            style={{ height: 28, width: '50%', backgroundColor: 'rgba(27,49,57,0.10)', marginBottom: 6 }}
          />
          <div
            className="animate-pulse rounded"
            style={{ height: 10, width: '70%', backgroundColor: 'rgba(27,49,57,0.06)' }}
          />
        </div>
      ))}
    </div>
  );
}

export function RegKPIs({ jurisdictionFilter }: RegKPIsProps) {
  const [cards, setCards] = useState<KPICard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const liveKpis = await fetchKPIs(jurisdictionFilter);
        if (cancelled) return;

        if (liveKpis) {
          const totalDocs = parseInt(liveKpis.total_documents) || 0;
          const federalDocs = parseInt(liveKpis.federal_docs) || 0;
          const stateDocs = parseInt(liveKpis.state_docs) || 0;
          const jurisdictions = parseInt(liveKpis.jurisdictions_covered) || 0;
          const docTypes = parseInt(liveKpis.document_types) || 0;
          const totalWords = parseInt(liveKpis.total_words) || 0;

          setCards([
            { label: 'Documents', value: totalDocs, color: LL_ACCENT, sub: 'In corpus' },
            { label: 'Jurisdictions', value: jurisdictions, color: LL_TEXT_PRIMARY, sub: 'States + Federal' },
            { label: 'Federal Docs', value: federalDocs, color: LL_TEXT_PRIMARY, sub: 'FCC orders/guidance' },
            { label: 'State Docs', value: stateDocs, color: LL_TEXT_PRIMARY, sub: 'PUC dockets/notices' },
            { label: 'Doc Types', value: docTypes, color: LL_TEXT_PRIMARY, sub: 'Categories' },
            { label: 'Total Words', value: totalWords > 1000 ? `${Math.round(totalWords / 1000)}K` : totalWords, color: LL_TEXT_PRIMARY, sub: 'Corpus size' },
          ]);
          setLoading(false);
          return;
        }
      } catch {
        // Fall through to mock
      }
      setLoading(false);

      if (cancelled) return;
      // Mock fallback
      setLoading(false);
      const mockKpis = getMockKPIs();
      setCards([
        { label: 'Jurisdictions', value: mockKpis.jurisdictions_covered, color: LL_TEXT_PRIMARY, sub: 'States covered' },
        { label: 'Pending Filings', value: mockKpis.pending_filings, color: LL_TEXT_PRIMARY, sub: 'Awaiting submission' },
        { label: 'Next Deadline', value: `${mockKpis.days_until_next_deadline}d`, color: LL_TEXT_PRIMARY, sub: 'Until next filing' },
        { label: 'Compliance', value: `${mockKpis.compliance_pct}%`, color: LL_TEXT_PRIMARY, sub: 'Overall rate' },
        { label: 'Overdue', value: mockKpis.overdue_items, color: LL_TEXT_PRIMARY, sub: 'Items past due' },
        { label: 'Documents', value: mockKpis.documents_indexed, color: LL_TEXT_PRIMARY, sub: 'Indexed for search' },
      ]);
    }

    load();
    return () => { cancelled = true; };
  }, [jurisdictionFilter]);

  if (loading && cards.length === 0) {
    return <KPISkeleton />;
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map((card) => (
        <div
          key={card.label}
          style={{
            background: '#FFFFFF',
            border: `1px solid ${LL_BORDER}`,
            borderRadius: 8,
            padding: 12,
          }}
        >
          <p
            role="status"
            aria-label={card.label}
            style={{
              fontSize: '0.75rem',
              color: LL_TEXT_SECONDARY,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              margin: 0,
            }}
          >
            {card.label}
          </p>
          <p
            style={{
              fontSize: '1.75rem',
              fontWeight: 700,
              color: card.color,
              margin: '4px 0 0',
              lineHeight: 1.2,
            }}
          >
            {card.value}
          </p>
          {card.sub && (
            <p
              style={{
                fontSize: '0.6875rem',
                color: LL_TEXT_SECONDARY,
                margin: '4px 0 0',
              }}
            >
              {card.sub}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
