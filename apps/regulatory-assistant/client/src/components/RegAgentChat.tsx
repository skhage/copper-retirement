/**
 * RegAgentChat.tsx
 * Chat interface to P6-REG regulatory RAG agent.
 * Screen 1 (Ask) — default landing.
 *
 * Live mode: searches fcc_regulatory_document corpus via /api/corpus/search
 * Fallback: uses pre-built Q&A pairs from mockData.ts
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { SuggestedQuestions } from './SuggestedQuestions';
import { searchCorpus, documentToCitation, composeAnswer } from '../api/corpus';
import { findMockAnswer } from '../mock/mockData';
import type { Citation } from '../mock/mockData';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  confidence?: 'high' | 'medium' | 'low';
  source?: 'live' | 'mock';
}

interface RegAgentChatProps {
  jurisdictionFilter: string;
  onCitationClick: (citation: Citation) => void;
}

export function RegAgentChat({ jurisdictionFilter, onCitationClick }: RegAgentChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim()) return;

    const userMsg: ChatMessage = { role: 'user', content: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      // Try live corpus search first
      const docs = await searchCorpus(question, jurisdictionFilter);
      if (docs.length > 0) {
        const answer = composeAnswer(docs, question);
        const citations: Citation[] = docs.slice(0, 4).map((doc, i) =>
          documentToCitation(doc, i)
        );
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: answer,
          citations,
          confidence: citations.some((c) => c.confidence === 'high') ? 'high' : 'medium',
          source: 'live',
        }]);
      } else {
        // No live results — fall back to mock Q&A
        const match = findMockAnswer(question);
        const assistantMsg: ChatMessage = match
          ? {
              role: 'assistant',
              content: match.answer,
              citations: match.citations,
              confidence: 'high',
              source: 'mock',
            }
          : {
              role: 'assistant',
              content: `No matching documents found in the regulatory corpus for that query. Try specific terms like "Section 214", "copper retirement", "notice", or a state name (CO, WA, OR, AZ, MN, ID).\n\nJurisdiction context: ${jurisdictionFilter === 'all' ? 'All states' : jurisdictionFilter}.`,
              citations: [],
              confidence: 'low',
            };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    } catch {
      // API error — graceful fallback to mock
      console.warn('[RegAgentChat] Live search unavailable, using mock fallback');
      const match = findMockAnswer(question);
      const assistantMsg: ChatMessage = match
        ? {
            role: 'assistant',
            content: match.answer,
            citations: match.citations,
            confidence: 'high',
            source: 'mock',
          }
        : {
            role: 'assistant',
            content: `I don't have specific guidance for that question. This may require review by the legal/regulatory team. Jurisdiction context: ${jurisdictionFilter === 'all' ? 'All states' : jurisdictionFilter}.`,
            citations: [],
            confidence: 'low',
            source: 'mock',
          };
      setMessages((prev) => [...prev, assistantMsg]);
    }

    setIsLoading(false);
  }, [jurisdictionFilter]);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  }, [input, sendMessage]);

  const handleSuggestedQuestion = useCallback((question: string) => {
    sendMessage(question);
  }, [sendMessage]);

  return (
    <div className="flex flex-col h-[calc(100vh-220px)]">
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <h2 className="text-xl font-semibold mb-2">Ask about regulatory requirements</h2>
            <p className="text-sm text-muted-foreground mb-6">
              Search 305 regulatory documents — FCC orders, state PUC dockets, guidance, and notice templates.
              {jurisdictionFilter !== 'all' && (
                <span className="block mt-1">Filtering for: <strong>{jurisdictionFilter}</strong></span>
              )}
            </p>
            <SuggestedQuestions onSelect={handleSuggestedQuestion} />
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>

              {/* Source indicator */}
              {msg.role === 'assistant' && msg.source === 'live' && (
                <div className="mt-1 text-xs text-green-700 flex items-center gap-1">
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#00A972', display: 'inline-block' }} />
                  Live corpus
                </div>
              )}

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-2 border-t border-muted-foreground/20">
                  {msg.citations.map((cite) => (
                    <button
                      key={cite.id}
                      onClick={() => onCitationClick(cite)}
                      className="flex items-start gap-2 text-xs text-left mt-1 hover:bg-background/50 rounded p-1 w-full transition-colors"
                    >
                      <span className="font-bold text-primary">[{cite.id}]</span>
                      <span className="text-muted-foreground">
                        {cite.document_title}, {cite.paragraph_ref}
                      </span>
                    </button>
                  ))}
                </div>
              )}

              {/* Confidence indicator */}
              {msg.role === 'assistant' && msg.confidence === 'low' && (
                <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
                  No matching documents found. Consider verifying with legal.
                  <button className="ml-2 underline font-medium">Escalate</button>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <span className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Search the regulatory corpus..."
          className="flex-1 border rounded-lg px-4 py-2 text-sm bg-background focus:outline-none focus:ring-2 focus:ring-primary"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
