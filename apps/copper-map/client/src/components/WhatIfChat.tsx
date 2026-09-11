/**
 * WhatIfChat.tsx
 * Genie Agent what-if analysis panel.
 * "What if we retire copper in Denver? How many customers? Revenue impact?"
 *
 * TODO: Connect to real Genie Agent endpoint when P6-SUPER is deployed.
 * Currently uses mock responses from retirementData.ts.
 */
import { useState, useRef, useEffect, useCallback } from 'react';
import {
  ChatMessage,
  SUGGESTED_QUESTIONS,
  generateMockResponse,
} from '../mock/retirementData';

export function WhatIfChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'sys-1',
      role: 'agent',
      content:
        'I can help you analyze the impact of retiring copper in any area. ' +
        'Ask about customer impact, revenue at risk, network disruption, ' +
        'costs, or regulatory constraints for any wire center or state.',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const sendMessage = useCallback(
    (text: string) => {
      if (!text.trim()) return;
      const userMsg: ChatMessage = {
        id: `u-${Date.now()}`,
        role: 'user',
        content: text.trim(),
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setInput('');
      setIsTyping(true);

      // Simulate agent response delay
      setTimeout(() => {
        const agentMsg = generateMockResponse(text);
        setMessages((prev) => [...prev, agentMsg]);
        setIsTyping(false);
      }, 800 + Math.random() * 600);
    },
    []
  );

  return (
    <div className="flex flex-col h-full bg-white border rounded-lg shadow-sm">
      {/* Header */}
      <div className="px-4 py-3 border-b">
        <h3 className="text-sm font-semibold">What-If Analysis</h3>
        <p className="text-xs text-muted-foreground">Ask about retirement impact scenarios</p>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3" style={{ maxHeight: 420 }}>
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[90%] rounded-lg px-3 py-2 text-sm ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-foreground'
              }`}
            >
              <p className="whitespace-pre-wrap" dangerouslySetInnerHTML={{
                __html: msg.content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
              }} />
              {msg.impact_summary && (
                <div className="mt-2 pt-2 border-t border-gray-200 grid grid-cols-2 gap-1 text-xs">
                  <div>Customers: <strong>{msg.impact_summary.total_customers_affected.toLocaleString()}</strong></div>
                  <div>Revenue: <strong>${(msg.impact_summary.total_revenue_impact_mrr / 1000).toFixed(1)}K MRR</strong></div>
                  <div>Cost: <strong>${(msg.impact_summary.total_cost / 1000).toFixed(0)}K</strong></div>
                  <div>Net: <strong>${(msg.impact_summary.net_cost / 1000).toFixed(0)}K</strong></div>
                  <div className="col-span-2">Services: <strong>{msg.impact_summary.services_disrupted}</strong></div>
                </div>
              )}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-3 py-2 text-sm text-muted-foreground">
              Analyzing scenario...
            </div>
          </div>
        )}
      </div>

      {/* Suggested questions */}
      {messages.length <= 2 && (
        <div className="px-4 pb-2 flex flex-wrap gap-1">
          {SUGGESTED_QUESTIONS.slice(0, 3).map((q) => (
            <button
              key={q}
              onClick={() => sendMessage(q)}
              className="text-xs px-2 py-1 border rounded-full hover:bg-blue-50 hover:border-blue-300 transition-colors text-muted-foreground"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="px-4 py-3 border-t">
        <form
          onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask: What if we retire copper in..."
            className="flex-1 text-sm border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isTyping}
          />
          <button
            type="submit"
            disabled={isTyping || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}
