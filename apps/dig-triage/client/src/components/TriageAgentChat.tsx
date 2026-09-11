/**
 * TriageAgentChat.tsx
 * Chat panel connected to P6-TRIAGE agent endpoint.
 * Shows agent analysis: reroute recommendations, affected customers,
 * priority scores. Human-in-loop approve/reject buttons per action.
 *
 * TODO: Implement SSE streaming once P6-TRIAGE Model Serving endpoint is deployed.
 * Currently uses mock agent responses.
 */
import { useState, useEffect, useRef } from 'react';
import { USE_MOCK_DATA, getMockAgentResponse, SEVERITY_COLORS } from '../mock/mockData';
import type { Incident, AgentResponse, AgentAction, ActionDecision } from '../mock/mockData';
import { formatHours, severityLabel } from '../lib/formatters';

interface TriageAgentChatProps {
  selectedIncident: Incident | null;
}

interface ChatMessage {
  role: 'user' | 'agent' | 'system';
  content: string;
  timestamp: string;
  agentResponse?: AgentResponse;
}

export function TriageAgentChat({ selectedIncident }: TriageAgentChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-trigger analysis when incident is selected
  useEffect(() => {
    if (!selectedIncident) return;

    const systemMsg: ChatMessage = {
      role: 'system',
      content: `Incident ${selectedIncident.incident_id} selected: ${selectedIncident.severity.toUpperCase()} ${selectedIncident.cable_damage_type} in ${selectedIncident.state}`,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, systemMsg]);
    triggerAnalysis(selectedIncident);
  }, [selectedIncident?.incident_id]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function triggerAnalysis(incident: Incident) {
    setIsLoading(true);

    const userMsg: ChatMessage = {
      role: 'user',
      content: `Analyze incident ${incident.incident_id}: ${incident.cable_damage_type} on ${incident.cable_type} cable. Root cause: ${incident.root_cause}. Affected pairs: ${incident.affected_pair_count}. Service interruption: ${incident.service_interruption ? 'YES' : 'NO'}.`,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    // Simulate agent thinking delay
    await new Promise((resolve) => setTimeout(resolve, 1200));

    const response = USE_MOCK_DATA
      ? getMockAgentResponse(incident.incident_id)
      : await fetchAgentResponse(incident); // TODO: implement

    const agentMsg: ChatMessage = {
      role: 'agent',
      content: response.message,
      timestamp: new Date().toISOString(),
      agentResponse: response,
    };
    setMessages((prev) => [...prev, agentMsg]);
    setIsLoading(false);
  }

  async function fetchAgentResponse(incident: Incident): Promise<AgentResponse> {
    // TODO: POST to /api/triage/chat with incident context
    // Implement SSE streaming for real-time agent responses
    return getMockAgentResponse(incident.incident_id);
  }

  function handleActionDecision(action: AgentAction, decision: ActionDecision) {
    console.log(`[triage-chat] Action ${action.action_id}: ${decision}`);
    // TODO: POST to /api/triage/action
    // Update action status in UI
    setMessages((prev) =>
      prev.map((msg) => {
        if (!msg.agentResponse) return msg;
        return {
          ...msg,
          agentResponse: {
            ...msg.agentResponse,
            actions: msg.agentResponse.actions.map((a) =>
              a.action_id === action.action_id ? { ...a, status: decision } : a
            ),
          },
        };
      })
    );
  }

  function handleSend() {
    if (!inputValue.trim()) return;
    const msg: ChatMessage = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, msg]);
    setInputValue('');
    // TODO: Send to agent endpoint
  }

  return (
    <div className="bg-card rounded-lg border shadow-sm flex flex-col h-[560px]">
      {/* Header */}
      <div className="p-3 border-b">
        <h2 className="text-sm font-semibold">Triage Agent</h2>
        <p className="text-xs text-muted-foreground">
          {selectedIncident
            ? `Analyzing ${selectedIncident.incident_id}`
            : 'Select an incident to begin analysis'}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-sm text-muted-foreground mt-8">
            <p className="font-medium">No incident selected</p>
            <p className="mt-1">Click an incident on the map to trigger agent analysis.</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
            {msg.role === 'system' ? (
              <div className="text-center text-xs text-muted-foreground py-1 italic">
                {msg.content}
              </div>
            ) : (
              <div
                className={`inline-block max-w-[95%] rounded-lg px-3 py-2 text-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-muted'
                }`}
              >
                <p>{msg.content}</p>

                {/* Agent confidence + sources */}
                {msg.agentResponse && (
                  <div className="mt-2 pt-2 border-t border-muted-foreground/20">
                    <p className="text-xs opacity-80">
                      Confidence: {(msg.agentResponse.confidence * 100).toFixed(0)}%
                      {' | '}
                      Sources: {msg.agentResponse.sources.join(', ')}
                    </p>
                  </div>
                )}

                {/* Agent actions with approve/reject */}
                {msg.agentResponse?.actions.map((action) => (
                  <div
                    key={action.action_id}
                    className="mt-2 p-2 rounded bg-background border text-foreground"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase" style={{
                        color: action.priority === 'critical' ? '#EB1600'
                          : action.priority === 'high' ? '#FF8C00'
                          : '#666',
                      }}>
                        {action.type} — {action.priority}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {action.affected_customers > 0 && `${action.affected_customers} customers`}
                        {action.estimated_time_hours > 0 && ` | ${formatHours(action.estimated_time_hours)}`}
                      </span>
                    </div>
                    <p className="text-xs mt-1">{action.description}</p>

                    {/* Human-in-loop buttons */}
                    {action.status === 'pending_approval' ? (
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={() => handleActionDecision(action, 'approved')}
                          className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleActionDecision(action, 'rejected')}
                          className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                        >
                          Reject
                        </button>
                      </div>
                    ) : (
                      <span className={`inline-block mt-2 text-xs px-2 py-0.5 rounded ${
                        action.status === 'approved'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {action.status.toUpperCase()}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="text-left">
            <div className="inline-block bg-muted rounded-lg px-3 py-2 text-sm">
              <span className="animate-pulse">Agent analyzing incident...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask the triage agent..."
            className="flex-1 border rounded px-3 py-1.5 text-sm"
            disabled={!selectedIncident}
          />
          <button
            onClick={handleSend}
            disabled={!selectedIncident || !inputValue.trim()}
            className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
