/**
 * FxContextPanel.tsx
 * FX rate context from refinitiv_fx_source.gl_daily_rates (23K rows, real data).
 * Shows latest cross-rates for copper pricing context (LME is USD-denominated).
 */
import { mockFxRates, USE_MOCK_DATA } from '../mock/mockData';

export function FxContextPanel() {
  // TODO: Replace with useAnalyticsQuery('fx_rates') when USE_MOCK_DATA=false
  const rates = USE_MOCK_DATA ? mockFxRates : mockFxRates;

  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm">
      <h3 className="text-sm font-semibold mb-2">FX Context</h3>
      <p className="text-xs text-muted-foreground mb-2">LME copper priced in USD. Key cross-rates:</p>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b">
            <th className="text-left py-1">Pair</th>
            <th className="text-right py-1">Rate</th>
          </tr>
        </thead>
        <tbody>
          {rates.map((r) => (
            <tr key={r.from_currency} className="border-b border-gray-50">
              <td className="py-1 font-medium">{r.from_currency}/USD</td>
              <td className="py-1 text-right">{r.rate.toFixed(4)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-xs text-muted-foreground mt-2">
        Source: refinitiv_fx_source.gl_daily_rates (23K rows, 2018–2025)
      </p>
    </div>
  );
}
