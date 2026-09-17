/**
 * RegAgentChat.tsx
 * Chat interface to P6-REG regulatory RAG agent.
 * Screen 1 (Ask) — default landing.
 *
 * Primary: calls /api/agent/chat (Vector Search + FMAPI RAG chain)
 * Fallback: corpus keyword search, then mock Q&A pairs
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { SuggestedQuestions } from './SuggestedQuestions';
import { askRegulatory } from '../api/ragChat';
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

/**
 * Parse LLM answer text and convert [Source N] references into clickable
 * superscript citation links that trigger the CitationSidebar.
 */
function renderContent(
  content: string,
  citations: Citation[] | undefined,
  onCitationClick: (citation: Citation) => void
) {
  if (!citations || citations.length === 0) {
    return <span className="whitespace-pre-wrap">{content}</span>;
  }

  // Split by [Source N] patterns (preserved as capture groups)
  const parts = content.split(/(\[Source \d+\])/g);

  return (
    <>
      {parts.map((part, i) => {
        const match = part.match(/^\[Source (\d+)\]$/);
        if (match) {
          const sourceNum = parseInt(match[1], 10);
          const citation = citations.find((c) => c.id === sourceNum);
          if (citation) {
            return (
              <button
                key={i}
                onClick={(e) => { e.stopPropagation(); onCitationClick(citation); }}
                className="inline-flex items-center align-super cursor-pointer"
                style={{
                  color: '#FF3621',
                  fontWeight: 700,
                  fontSize: '0.72em',
                  lineHeight: 1,
                  padding: '0 1px',
                  textDecoration: 'underline',
                  textDecorationStyle: 'dotted',
                  textUnderlineOffset: '2px',
                  background: 'none',
                  border: 'none',
                }}
                title={`${citation.document_title} \u2014 ${citation.paragraph_ref || 'View source'}`}
              >
                [{sourceNum}]
              </button>
            );
          }
          // Source ref with no matching citation
          return <span key={i} className="text-muted-foreground text-xs align-super">{part}</span>;
        }
        return <span key={i} className="whitespace-pre-wrap">{part}</span>;
      })}
    </>
  );
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
      // Call RAG endpoint (VS retrieval + FMAPI generation)
      const result = await askRegulatory(question, jurisdictionFilter);

      if (result.source_type === 'rag' || result.source_type === 'corpus') {
        // RAG or corpus search returned results
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: result.answer,
          citations: result.citations,
          confidence: result.citations.some((c) => c.confidence === 'high') ? 'high' : 'medium',
          source: result.source_type === 'rag' ? 'live' : 'live',
        }]);
      } else {
        // RAG + corpus both failed — fall back to mock Q&A
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
              content: result.answer,
              citations: [],
              confidence: 'low',
            };
        setMessages((prev) => [...prev, assistantMsg]);
      }
    } catch {
      // Unexpected error — graceful fallback to mock
      console.warn('[RegAgentChat] RAG pipeline unavailable, using mock fallback');
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
    <div className="flex flex-col flex-1 min-h-0" style={{ minHeight: '400px' }}>
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.length === 0 && (
          <div className="py-8">
            {jurisdictionFilter !== 'all' && (
              <div className="text-center mb-4">
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium" style={{ backgroundColor: 'rgba(0,169,114,0.12)', color: '#00A972' }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#00A972', display: 'inline-block' }} />
                  Filtering: {jurisdictionFilter}
                </span>
              </div>
            )}
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
              <div className="text-sm leading-relaxed">
                {msg.role === 'assistant'
                  ? renderContent(msg.content, msg.citations, onCitationClick)
                  : <span className="whitespace-pre-wrap">{msg.content}</span>
                }
              </div>

              {/* Source indicator */}
              {msg.role === 'assistant' && msg.source === 'live' && (
                <div className="mt-1 text-xs flex items-center gap-1" style={{ color: '#00A972' }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#00A972', display: 'inline-block' }} />
                  RAG — Vector Search + LLM
                </div>
              )}
              {msg.role === 'assistant' && msg.source === 'mock' && (
                <div className="mt-1 text-xs flex items-center gap-1" style={{ color: '#6E8898' }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#6E8898', display: 'inline-block' }} />
                  Mock data (offline fallback)
                </div>
              )}

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-2 border-t border-muted-foreground/20">
                  <p className="text-xs font-medium mb-1.5" style={{ color: '#6E8898' }}>
                    Sources ({msg.citations.length})
                  </p>
                  {msg.citations.map((cite) => (
                    <button
                      key={cite.id}
                      onClick={() => onCitationClick(cite)}
                      className="flex items-start gap-2 text-xs text-left mt-1.5 rounded p-2 w-full transition-colors"
                      style={{
                        border: '1px solid transparent',
                        backgroundColor: 'transparent',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(27,49,57,0.04)';
                        e.currentTarget.style.borderColor = 'rgba(27,49,57,0.12)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                        e.currentTarget.style.borderColor = 'transparent';
                      }}
                    >
                      <span className="font-bold shrink-0" style={{ color: '#FF3621' }}>[{cite.id}]</span>
                      <div className="min-w-0 flex-1">
                        <p className="font-medium truncate" style={{ color: '#1B3139' }}>
                          {cite.document_title}
                        </p>
                        <p style={{ color: '#6E8898' }}>
                          {cite.doc_id && <span className="font-mono" style={{ fontSize: '0.7rem' }}>{cite.doc_id}</span>}
                           {cite.doc_id && cite.paragraph_ref && ' \u00B7 '}
                           {cite.paragraph_ref}
                          {cite.jurisdiction && cite.jurisdiction !== 'Federal' && ` \u00B7 ${cite.jurisdiction}`}
                          {cite.effective_date && cite.effective_date !== 'N/A' && ` \u00B7 ${cite.effective_date}`}
                        </p>
                      </div>
                      <span className="shrink-0 px-1.5 py-0.5 rounded font-medium" style={{
                        fontSize: '10px',
                        backgroundColor: cite.confidence === 'high' ? 'rgba(0,169,114,0.15)' :
                          cite.confidence === 'medium' ? 'rgba(217,119,6,0.15)' : 'rgba(255,54,33,0.15)',
                        color: cite.confidence === 'high' ? '#00A972' :
                          cite.confidence === 'medium' ? '#D97706' : '#FF3621',
                      }}>
                        {cite.confidence}
                      </span>
                    </button>
                  ))}
                </div>
              )}

              {/* Confidence / empty-results indicator */}
              {msg.role === 'assistant' && msg.confidence === 'low' && (
                <div className="mt-2 p-2 rounded text-xs" style={{
                  backgroundColor: 'rgba(255,54,33,0.08)',
                  border: '1px solid rgba(255,54,33,0.3)',
                  color: '#FF3621',
                }}>
                  <div className="flex items-center gap-1.5">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                      <line x1="12" y1="9" x2="12" y2="13" />
                      <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                    <span>Low confidence — no strong document matches. Consider verifying with the legal/regulatory team.</span>
                  </div>
                </div>
              )}
              {/* Zero sources on a live answer */}
              {msg.role === 'assistant' && msg.citations && msg.citations.length === 0 && msg.confidence !== 'low' && msg.source === 'live' && (
                <div className="mt-2 p-2 rounded text-xs" style={{
                  backgroundColor: 'rgba(27,49,57,0.04)',
                  border: '1px solid rgba(27,49,57,0.12)',
                  color: '#6E8898',
                }}>
                  No source documents were cited for this answer. Results may be general knowledge rather than corpus-grounded.
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg px-4 py-3 max-w-[80%]">
              <div className="space-y-2.5">
                <div className="flex items-center gap-2 text-xs">
                  <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: '#00A972' }} />
                  <span style={{ color: '#00A972' }}>Searching 528 regulatory documents...</span>
                </div>
                <div className="space-y-1.5">
                  <div className="h-3 rounded animate-pulse w-full" style={{ backgroundColor: 'rgba(27,49,57,0.08)' }} />
                  <div className="h-3 rounded animate-pulse w-4/5" style={{ backgroundColor: 'rgba(27,49,57,0.06)' }} />
                  <div className="h-3 rounded animate-pulse w-3/5" style={{ backgroundColor: 'rgba(27,49,57,0.04)' }} />
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: '#6E8898' }} />
                  <span style={{ color: '#6E8898' }}>Generating answer from LLM...</span>
                </div>
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
          placeholder="Ask a regulatory question (e.g., 'What notice is required for copper retirement?')"
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
