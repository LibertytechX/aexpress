'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Realtime } from 'ably';
import { ChatsAPI, AblyTokenAPI, type ChatConversation, type ChatMessage } from '@/lib/api';

export default function SupportPage() {
  const [conversation, setConversation] = useState<ChatConversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ablyRef = useRef<Realtime | null>(null);
  const channelRef = useRef<any>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // ── Boot: get/create conversation + subscribe Ably ──────────────
  const boot = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [convo, tokenData] = await Promise.all([
        ChatsAPI.startConversation(),
        AblyTokenAPI.getToken(),
      ]);
      setConversation(convo);

      // Load history
      const history = await ChatsAPI.getMessages(convo.id);
      setMessages(history);

      // Mark read on open
      ChatsAPI.markRead(convo.id).catch(() => { });

      // Subscribe Ably
      const client = new Realtime({ token: tokenData.token });
      ablyRef.current = client;
      const channelName = `chat:customer:${(convo as any).user_id?.id || ''}`;
      const ch = client.channels.get(channelName);
      channelRef.current = ch;
      ch.subscribe('new_message', (msg: any) => {
        const d = msg.data as ChatMessage;
        setMessages(prev => {
          if (prev.find(m => m.id === d.id)) return prev;
          return [...prev, d];
        });
      });
    } catch (e: any) {
      setError(e.message || 'Could not connect to support. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    boot();
    return () => {
      channelRef.current?.unsubscribe();
      ablyRef.current?.close();
    };
  }, [boot]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const content = input.trim();
    if (!content || !conversation || sending) return;
    setSending(true);
    setInput('');
    try {
      const msg = await ChatsAPI.sendMessage(conversation.id, content);
      setMessages(prev => {
        if (prev.find(m => m.id === msg.id)) return prev;
        return [...prev, msg];
      });
    } catch (e: any) {
      setError(e.message || 'Failed to send message.');
    } finally {
      setSending(false);
    }
  };

  const fmt = (ts: string) =>
    new Date(ts).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });

  return (
    <div className="min-h-screen bg-gray-50" style={{ fontFamily: 'Inter, sans-serif' }}>
      {/* Page Header */}
      <div className="max-w-2xl mx-auto px-4 pt-8 pb-4">
        <h1 className="text-2xl font-bold text-gray-900">Support Chat</h1>
        <p className="text-sm text-gray-500 mt-1">
          Send us a message and we&apos;ll get back to you as soon as possible.
        </p>
      </div>

      {/* Chat Card */}
      <div
        className="max-w-2xl mx-auto mx-4 shadow-lg rounded-2xl overflow-hidden"
        style={{ height: 'calc(100vh - 180px)', display: 'flex', flexDirection: 'column', background: '#fff', border: '1px solid #e5e7eb' }}
      >
        {/* Chat header */}
        <div style={{ padding: '14px 20px', background: '#1B2A4A', display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 38, height: 38, borderRadius: 12, background: 'rgba(232,168,56,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18 }}>
            💬
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#fff' }}>AXpress Support</div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.55)', display: 'flex', alignItems: 'center', gap: 5 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80', display: 'inline-block' }} />
              Online · Usually replies within minutes
            </div>
          </div>
        </div>

        {/* Messages area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {loading && (
            <div style={{ textAlign: 'center', color: '#94a3b8', fontSize: 13, marginTop: 40 }}>
              Connecting to support…
            </div>
          )}
          {error && !loading && (
            <div style={{ background: '#fee2e2', color: '#dc2626', borderRadius: 12, padding: '12px 16px', fontSize: 13, fontWeight: 600 }}>
              ⚠️ {error}
              <button onClick={boot} style={{ marginLeft: 10, textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626', fontSize: 13 }}>
                Retry
              </button>
            </div>
          )}
          {!loading && !error && messages.length === 0 && (
            <div style={{ textAlign: 'center', marginTop: 40 }}>
              <div style={{ fontSize: 40, marginBottom: 8 }}>👋</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: '#1B2A4A' }}>Hi there!</div>
              <div style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
                How can we help you today? Send us a message below.
              </div>
            </div>
          )}
          {messages.map(m => {
            const isAgent = m.sender_type === 'agent';
            return (
              <div key={m.id} style={{ display: 'flex', justifyContent: isAgent ? 'flex-start' : 'flex-end' }}>
                {isAgent && (
                  <div style={{ width: 28, height: 28, borderRadius: 8, background: '#E8A838', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 800, color: '#fff', flexShrink: 0, marginRight: 8, alignSelf: 'flex-end' }}>
                    AX
                  </div>
                )}
                <div style={{ maxWidth: '70%' }}>
                  <div style={{
                    padding: '10px 14px',
                    borderRadius: 16,
                    borderBottomLeftRadius: isAgent ? 4 : 16,
                    borderBottomRightRadius: isAgent ? 16 : 4,
                    background: isAgent ? '#f1f5f9' : '#1B2A4A',
                    color: isAgent ? '#1B2A4A' : '#fff',
                    fontSize: 13,
                    lineHeight: 1.5,
                  }}>
                    {m.content}
                  </div>
                  <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 3, textAlign: isAgent ? 'left' : 'right', paddingLeft: isAgent ? 4 : 0, paddingRight: isAgent ? 0 : 4 }}>
                    {fmt(m.timestamp)}
                  </div>
                </div>
              </div>
            );
          })}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        {!loading && !error && (
          <div style={{ padding: '12px 16px', borderTop: '1px solid #e5e7eb', display: 'flex', gap: 8, alignItems: 'center' }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder="Type a message…"
              disabled={sending}
              style={{
                flex: 1,
                border: '1.5px solid #e5e7eb',
                borderRadius: 12,
                padding: '10px 14px',
                fontSize: 13,
                outline: 'none',
                color: '#1B2A4A',
                fontFamily: 'inherit',
                background: sending ? '#f8fafc' : '#fff',
              }}
            />
            <button
              onClick={sendMessage}
              disabled={sending || !input.trim()}
              style={{
                width: 42,
                height: 42,
                borderRadius: 12,
                border: 'none',
                background: sending || !input.trim() ? '#e5e7eb' : 'linear-gradient(135deg,#E8A838,#F5C563)',
                color: sending || !input.trim() ? '#94a3b8' : '#1B2A4A',
                cursor: sending || !input.trim() ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'all 0.15s',
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
