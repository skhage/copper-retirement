/**
 * LakeLinkHeader.tsx
 * Shared nav header for all Lakelink Fiber apps (BRAND_GUIDE §6 Nav Header).
 *
 * Spec:
 *   - Left: "Lakelink Fiber" wordmark (text, --ll-secondary #1B3139, 600 weight, 16px)
 *   - Left: App subtitle (muted, 13px)
 *   - Right: Data source badge (LIVE/MOCK + SYNTHETIC)
 *   - Background: --ll-surface #F9F7F4 with bottom border #E5E2DD
 *
 * Import this in all 5 apps for visual consistency.
 * For Dash (Python) apps, use lakelink_header() in app.py.
 */
import { USE_MOCK_DATA } from '../mock/retirementData';

/* Lakelink Fiber brand tokens */
const LL_SECONDARY = '#1B3139';
const LL_SURFACE = '#F9F7F4';
const LL_TEXT_SECONDARY = '#6E8898';
const LL_BORDER = '#E5E2DD';
const LL_INFO = '#60A5FA';
const LL_MEDIUM = '#FFD700';

export interface LakeLinkHeaderProps {
  /** App subtitle shown below wordmark, e.g. "Copper Retirement Impact Map" */
  subtitle: string;
  /** Optional tagline below subtitle */
  tagline?: string;
  /** Override data source: 'LIVE' | 'MOCK'. Defaults to mock detection. */
  dataSource?: 'LIVE' | 'MOCK';
  /** Whether to show the SYNTHETIC badge. Defaults true. */
  showSynthetic?: boolean;
}

export function LakeLinkHeader({
  subtitle,
  tagline,
  dataSource,
  showSynthetic = true,
}: LakeLinkHeaderProps) {
  const source = dataSource ?? (USE_MOCK_DATA ? 'MOCK' : 'LIVE');
  const badgeColor = source === 'LIVE' ? LL_INFO : LL_MEDIUM;

  return (
    <header
      style={{
        background: LL_SURFACE,
        borderBottom: `1px solid ${LL_BORDER}`,
        padding: '16px 24px 12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontFamily: 'Inter, system-ui, sans-serif',
      }}
    >
      {/* Left: wordmark + subtitle */}
      <div>
        <p
          style={{
            fontSize: '1rem',
            fontWeight: 600,
            color: LL_SECONDARY,
            lineHeight: 1.2,
            margin: 0,
          }}
        >
          Lakelink Fiber
        </p>
        <h1
          style={{
            fontSize: '1.5rem',
            fontWeight: 700,
            color: LL_SECONDARY,
            margin: '4px 0 0',
            lineHeight: 1.2,
          }}
        >
          {subtitle}
        </h1>
        {tagline && (
          <p
            style={{
              fontSize: '0.8125rem',
              color: LL_TEXT_SECONDARY,
              margin: '2px 0 0',
            }}
          >
            {tagline}
          </p>
        )}
      </div>

      {/* Right: data source badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span
          style={{
            fontSize: '0.6875rem',
            padding: '4px 10px',
            borderRadius: 4,
            backgroundColor: `${badgeColor}33`,
            color: LL_SECONDARY,
            fontWeight: 500,
          }}
        >
          {source} DATA{showSynthetic ? ' \u00B7 SYNTHETIC' : ''}
        </span>
      </div>
    </header>
  );
}
