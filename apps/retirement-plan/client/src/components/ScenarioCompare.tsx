/**
 * ScenarioCompare.tsx
 * Side-by-side comparison of P4-SEQ optimizer scenarios.
 * Shows: scenario name, objective, total cost, duration, waves, risk score.
 * Active scenario highlighted. Switch-active button.
 *
 * TODO: Once P4-SEQ deploys, replace mock with live scenario runs from MLflow.
 */
import { useState } from 'react';
import { mockScenarios } from '../mock/mockData';
import { formatCurrency } from '../lib/formatters';
import type { ScenarioRun } from '../mock/mockData';

export function ScenarioCompare() {
  const [scenarios, setScenarios] = useState(mockScenarios);

  const handleSetActive = (scenarioId: string) => {
    setScenarios(
      scenarios.map((s) => ({
        ...s,
        status: s.scenario_id === scenarioId ? 'active' as const : s.status === 'active' ? 'draft' as const : s.status,
      }))
    );
  };

  const riskColor = (score: number) =>
    score >= 80 ? 'text-red-600' : score >= 60 ? 'text-amber-600' : 'text-green-600';

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold">Optimizer Scenarios</h2>
        <button
          className="text-xs bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700 transition-colors"
          onClick={() => {
            console.log('[retirement-plan] Requesting new scenario run...');
            // TODO: POST /api/plan/scenario when P4-SEQ is available
          }}
        >
          + New Scenario Run
        </button>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {scenarios.map((s) => (
          <div
            key={s.scenario_id}
            className={`rounded-lg border p-4 transition-all ${
              s.status === 'active'
                ? 'ring-2 ring-blue-500 bg-blue-50/50'
                : 'hover:border-blue-300'
            }`}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold">{s.name}</h3>
              <span
                className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                  s.status === 'active'
                    ? 'bg-green-100 text-green-700'
                    : s.status === 'draft'
                    ? 'bg-slate-100 text-slate-600'
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {s.status}
              </span>
            </div>

            {/* Objective */}
            <p className="text-xs text-muted-foreground mb-3">{s.objective}</p>

            {/* Metrics grid */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div>
                <p className="text-[10px] text-muted-foreground">Total Cost</p>
                <p className="text-sm font-bold">{formatCurrency(s.total_cost)}</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">Duration</p>
                <p className="text-sm font-bold">{s.total_duration_months}mo</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">Waves</p>
                <p className="text-sm font-bold">{s.waves_used}</p>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground">Risk Score</p>
                <p className={`text-sm font-bold ${riskColor(s.risk_score)}`}>
                  {s.risk_score}/100
                </p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              {s.status !== 'active' && (
                <button
                  onClick={() => handleSetActive(s.scenario_id)}
                  className="text-xs bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700 transition-colors"
                >
                  Set Active
                </button>
              )}
              <button className="text-xs border px-2 py-1 rounded hover:bg-muted transition-colors">
                View Detail
              </button>
            </div>
          </div>
        ))}
      </div>

      <p className="text-[10px] text-muted-foreground mt-3">
        Scenarios from P4-SEQ optimizer (mock data — optimizer not yet deployed).
        Created {mockScenarios[0]?.created_at}.
      </p>
    </div>
  );
}
