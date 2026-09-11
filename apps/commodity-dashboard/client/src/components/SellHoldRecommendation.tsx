/**
 * SellHoldRecommendation.tsx
 * Sell/Hold/Accumulate recommendation card from P4-COMMODITY model.
 * Shows recommendation badge, confidence, price targets, and reasoning.
 */
import { mockRecommendation, USE_MOCK_DATA } from '../mock/mockData';
import { formatPriceLb, formatPercent, formatDate } from '../lib/formatters';
import { recommendationColor } from '../lib/formatters';

export function SellHoldRecommendation() {
  const rec = USE_MOCK_DATA ? mockRecommendation : mockRecommendation;

  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm">
      <h3 className="text-sm font-semibold mb-3">AI Recommendation</h3>

      {/* Badge */}
      <div className="flex items-center gap-3 mb-3">
        <span className={`text-xl font-bold px-3 py-1 rounded ${recommendationColor(rec.recommendation)}`}>
          {rec.recommendation}
        </span>
        <span className="text-sm text-muted-foreground">
          {formatPercent(rec.confidence * 100)} confidence
        </span>
      </div>

      {/* Price targets */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="text-center">
          <p className="text-xs text-muted-foreground">Current</p>
          <p className="text-sm font-semibold">{formatPriceLb(rec.current_spot)}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-muted-foreground">3-mo Target</p>
          <p className="text-sm font-semibold text-blue-600">{formatPriceLb(rec.forecast_3m)}</p>
        </div>
        <div className="text-center">
          <p className="text-xs text-muted-foreground">12-mo Target</p>
          <p className="text-sm font-semibold text-blue-600">{formatPriceLb(rec.forecast_12m)}</p>
        </div>
      </div>

      {/* Reasoning */}
      <p className="text-xs text-muted-foreground leading-relaxed">
        {rec.reasoning}
      </p>

      <p className="text-xs text-muted-foreground mt-2 italic">
        Updated: {formatDate(rec.updated_at)} (mock — P4-COMMODITY model pending)
      </p>
    </div>
  );
}
