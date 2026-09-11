/**
 * IncidentForm.tsx
 * Modal form for reporting a new dig-safe incident.
 * Captures: location (lat/lon), severity, cable type, root cause,
 * contractor, damage description.
 *
 * TODO: Lat/lon click-on-map integration once deck.gl is installed.
 * TODO: Write to Lakebase `dig_incidents` table once P5-SCHEMA lands.
 * Currently submits to /api/triage/incident (mock endpoint).
 */
import { useState } from 'react';
import { SEVERITY_LEVELS, getMockStates } from '../mock/mockData';
import type { Severity, CableType } from '../mock/mockData';

interface IncidentFormProps {
  onClose: () => void;
  onSubmit: (incident: Record<string, unknown>) => void;
}

const CABLE_TYPES: CableType[] = ['aerial', 'buried_direct', 'underground_conduit'];
const ROOT_CAUSES = [
  'excavation', 'boring', 'trenching', 'plowing',
  'hand_dig', 'natural_event', 'vehicle_strike', 'utility_conflict',
];

export function IncidentForm({ onClose, onSubmit }: IncidentFormProps) {
  const [severity, setSeverity] = useState<Severity>('major');
  const [state, setState] = useState('CO');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [cableType, setCableType] = useState<CableType>('buried_direct');
  const [rootCause, setRootCause] = useState('excavation');
  const [description, setDescription] = useState('');
  const [contractorAtFault, setContractorAtFault] = useState(false);
  const [oneCallFiled, setOneCallFiled] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      severity,
      state,
      latitude: parseFloat(latitude),
      longitude: parseFloat(longitude),
      cable_type: cableType,
      root_cause: rootCause,
      description,
      contractor_at_fault: contractorAtFault,
      one_call_ticket_submitted: oneCallFiled,
      incident_timestamp: new Date().toISOString(),
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
      <div className="bg-card rounded-lg border shadow-xl w-[520px] max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-bold text-red-600">Report New Incident</h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-xl leading-none"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Severity + State */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium mb-1">Severity</label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value as Severity)}
                className="w-full border rounded px-2 py-1.5 text-sm"
              >
                {SEVERITY_LEVELS.map((s) => (
                  <option key={s} value={s}>{s.toUpperCase()}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">State</label>
              <select
                value={state}
                onChange={(e) => setState(e.target.value)}
                className="w-full border rounded px-2 py-1.5 text-sm"
              >
                {getMockStates().map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Location */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium mb-1">Latitude</label>
              <input
                type="number"
                step="0.0001"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
                placeholder="e.g., 39.7392"
                className="w-full border rounded px-2 py-1.5 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Longitude</label>
              <input
                type="number"
                step="0.0001"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
                placeholder="e.g., -104.9903"
                className="w-full border rounded px-2 py-1.5 text-sm"
                required
              />
            </div>
          </div>
          <p className="text-xs text-muted-foreground -mt-2">
            TODO: Click-on-map to set coordinates (requires deck.gl integration)
          </p>

          {/* Cable type + Root cause */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium mb-1">Cable Type</label>
              <select
                value={cableType}
                onChange={(e) => setCableType(e.target.value as CableType)}
                className="w-full border rounded px-2 py-1.5 text-sm"
              >
                {CABLE_TYPES.map((t) => (
                  <option key={t} value={t}>{t.replace('_', ' ')}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Root Cause</label>
              <select
                value={rootCause}
                onChange={(e) => setRootCause(e.target.value)}
                className="w-full border rounded px-2 py-1.5 text-sm"
              >
                {ROOT_CAUSES.map((c) => (
                  <option key={c} value={c}>{c.replace('_', ' ')}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Checkboxes */}
          <div className="flex gap-6">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={contractorAtFault}
                onChange={(e) => setContractorAtFault(e.target.checked)}
              />
              Contractor at fault
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={oneCallFiled}
                onChange={(e) => setOneCallFiled(e.target.checked)}
              />
              811 One-call filed
            </label>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-medium mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full border rounded px-2 py-1.5 text-sm"
              placeholder="Describe the incident, damage observed, and immediate actions taken..."
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm border rounded-md hover:bg-muted"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              Submit Incident
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
