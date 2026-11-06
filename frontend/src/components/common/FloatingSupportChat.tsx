'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Realtime } from 'ably';
import { ChatsAPI, AblyTokenAPI, type ChatConversation, type ChatMessage } from '@/lib/api';

/* ─── Floating Support Chat ─────────────────────────────────────────
   A self-contained floating chat button + panel that can be injected
   into any page. Renders a fixed bottom-right button; clicking it
   slides open a premium chat panel powered by the same Ably real-time
   backend as the /support page.
─────────────────────────────────────────────────────────────────── */

export default function FloatingSupportChat() {
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(false);
  const [conversation, setConversation] = useState<ChatConversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [booted, setBooted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ablyRef = useRef<Realtime | null>(null);
  const channelRef = useRef<any>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // ── Boot: only on first open ──────────────────────────────────────
  const boot = useCallback(async () => {
    if (booted) return;
    setLoading(true);
    setError(null);
    try {
      const [convo, tokenData] = await Promise.all([
        ChatsAPI.startConversation(),
        AblyTokenAPI.getToken(),
      ]);
      setConversation(convo);

      const history = await ChatsAPI.getMessages(convo.id);
      setMessages(history);
      ChatsAPI.markRead(convo.id).catch(() => { });

      const client = new Realtime({ token: tokenData.token });
      ablyRef.current = client;
      const channelName = `chat:${convo.type}:${(convo as any).participant?.id || ''}`;
      const ch = client.channels.get(channelName);
      channelRef.current = ch;
      ch.subscribe('new_message', (msg: any) => {
        const d = msg.data as ChatMessage;
        setMessages(prev => {
          if (prev.find(m => m.id === d.id)) return prev;
          return [...prev, d];
        });
        // Show unread dot if panel is closed
        setUnread(prev => true);
      });
      setBooted(true);
    } catch (e: any) {
      setError(e.message || 'Could not connect to support.');
    } finally {
      setLoading(false);
    }
  }, [booted]);

  // Cleanup Ably on unmount
  useEffect(() => {
    return () => {
      channelRef.current?.unsubscribe();
      ablyRef.current?.close();
    };
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (open) {
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  }, [messages, open]);

  // On open: boot if first time, clear unread, focus input
  useEffect(() => {
    if (open) {
      boot();
      setUnread(false);
      if (conversation) ChatsAPI.markRead(conversation.id).catch(() => { });
      setTimeout(() => inputRef.current?.focus(), 350);
    }
  }, [open, boot, conversation]);

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
      setError(e.message || 'Failed to send.');
    } finally {
      setSending(false);
    }
  };

  const fmt = (ts: string) =>
    new Date(ts).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });

  const panelVisible = open;

  return (
    <>
      {/* ─── Floating Button ─── */}
      <button
        onClick={() => setOpen(o => !o)}
        aria-label="Open support chat"
        style={{
          position: 'fixed',
          bottom: 28,
          right: 28,
          zIndex: 9001,
          width: 56,
          height: 56,
          borderRadius: '50%',
          border: 'none',
          cursor: 'pointer',
          background: 'linear-gradient(135deg, #E8A838 0%, #F5C563 100%)',
          boxShadow: '0 8px 24px rgba(232,168,56,0.45), 0 2px 8px rgba(0,0,0,0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'transform 0.2s ease, box-shadow 0.2s ease',
          transform: open ? 'scale(0.93)' : 'scale(1)',
        }}
        onMouseEnter={e => { if (!open) (e.currentTarget as HTMLElement).style.transform = 'scale(1.08)'; }}
        onMouseLeave={e => { (e.currentTarget as HTMLElement).style.transform = open ? 'scale(0.93)' : 'scale(1)'; }}
      >
        {/* Unread badge */}
        {unread && !open && (
          <span style={{
            position: 'absolute',
            top: 6,
            right: 6,
            width: 11,
            height: 11,
            borderRadius: '50%',
            background: '#ef4444',
            border: '2px solid #fff',
            display: 'block',
          }} />
        )}

        {/* Icon — chat when closed, X when open */}
        <span style={{ color: '#1B2A4A', display: 'flex', transition: 'opacity 0.15s' }}>
          {open ? (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          ) : (
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z" />
            </svg>
          )}
        </span>
      </button>

      {/* ─── Chat Panel ─── */}
      <div
        style={{
          position: 'fixed',
          bottom: 96,
          right: 24,
          zIndex: 9000,
          width: 370,
          maxWidth: 'calc(100vw - 32px)',
          height: 520,
          maxHeight: 'calc(100vh - 120px)',
          borderRadius: 20,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          background: '#fff',
          boxShadow: '0 24px 64px rgba(0,0,0,0.18), 0 4px 16px rgba(0,0,0,0.08)',
          border: '1px solid rgba(255,255,255,0.6)',
          // Animation
          opacity: panelVisible ? 1 : 0,
          transform: panelVisible ? 'translateY(0) scale(1)' : 'translateY(24px) scale(0.97)',
          pointerEvents: panelVisible ? 'auto' : 'none',
          transition: 'opacity 0.25s cubic-bezier(0.34,1.56,0.64,1), transform 0.25s cubic-bezier(0.34,1.56,0.64,1)',
        }}
      >
        {/* ── Header ── */}
        <div style={{
          padding: '14px 18px',
          background: 'linear-gradient(135deg, #1B2A4A 0%, #0f1b33 100%)',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          flexShrink: 0,
        }}>
          {/* Avatar */}
          <div style={{
            width: 40,
            height: 40,
            borderRadius: 12,
            background: 'linear-gradient(135deg, #E8A838, #F5C563)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 18,
            flexShrink: 0,
            boxShadow: '0 4px 12px rgba(232,168,56,0.3)',
          }}>
            💬
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#fff', letterSpacing: '-0.2px' }}>
              AXpress Support
            </div>
            <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', display: 'flex', alignItems: 'center', gap: 5, marginTop: 1 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ade80', display: 'inline-block' }} />
              Online · Replies within minutes
            </div>
          </div>

          <button
            onClick={() => setOpen(false)}
            style={{
              background: 'rgba(255,255,255,0.08)',
              border: 'none',
              borderRadius: 8,
              width: 30,
              height: 30,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'rgba(255,255,255,0.6)',
              flexShrink: 0,
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.15)')}
            onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.08)')}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* ── Messages ── */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '14px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          background: '#f8fafc',
        }}>
          {loading && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 12 }}>
              <div style={{
                width: 32, height: 32,
                border: '3px solid #E8A838',
                borderTopColor: 'transparent',
                borderRadius: '50%',
                animation: 'fcSpin 0.7s linear infinite',
              }} />
              <span style={{ fontSize: 12, color: '#94a3b8', fontWeight: 500 }}>Connecting…</span>
            </div>
          )}

          {error && !loading && (
            <div style={{
              background: '#fef2f2', color: '#dc2626',
              borderRadius: 12, padding: '10px 14px',
              fontSize: 12, fontWeight: 600,
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              ⚠️ {error}
              <button onClick={boot} style={{ marginLeft: 'auto', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626', fontSize: 12 }}>
                Retry
              </button>
            </div>
          )}

          {!loading && !error && messages.length === 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', textAlign: 'center', color: '#64748b' }}>
              <div style={{
                width: 56, height: 56, borderRadius: 16,
                background: 'linear-gradient(135deg, #fef3c7, #fde68a)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 28, marginBottom: 12,
                boxShadow: '0 4px 12px rgba(232,168,56,0.2)',
              }}>
                👋
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#1B2A4A', marginBottom: 4 }}>Hi there!</div>
              <div style={{ fontSize: 12, color: '#94a3b8', lineHeight: 1.5 }}>
                How can we help you today?<br />Send us a message below.
              </div>
            </div>
          )}

          {messages.map(m => {
            const isAgent = m.sender_type === 'agent';
            return (
              <div key={m.id} style={{ display: 'flex', justifyContent: isAgent ? 'flex-start' : 'flex-end', gap: 8 }}>
                {isAgent && (
                  <div style={{
                    width: 26, height: 26, borderRadius: 8,
                    background: '#E8A838',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 10, fontWeight: 800, color: '#1B2A4A',
                    flexShrink: 0, alignSelf: 'flex-end',
                  }}>
                    AX
                  </div>
                )}
                <div style={{ maxWidth: '78%' }}>
                  <div style={{
                    padding: '9px 13px',
                    borderRadius: 16,
                    borderBottomLeftRadius: isAgent ? 4 : 16,
                    borderBottomRightRadius: isAgent ? 16 : 4,
                    background: isAgent ? '#fff' : 'linear-gradient(135deg, #1B2A4A, #243554)',
                    color: isAgent ? '#1B2A4A' : '#fff',
                    fontSize: 13,
                    lineHeight: 1.55,
                    boxShadow: isAgent
                      ? '0 1px 4px rgba(0,0,0,0.06)'
                      : '0 2px 8px rgba(27,42,74,0.25)',
                    border: isAgent ? '1px solid #e2e8f0' : 'none',
                  }}>
                    {m.content}
                  </div>
                  <div style={{
                    fontSize: 10, color: '#94a3b8', marginTop: 3,
                    textAlign: isAgent ? 'left' : 'right',
                    paddingLeft: isAgent ? 4 : 0, paddingRight: isAgent ? 0 : 4,
                  }}>
                    {fmt(m.timestamp)}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Typing indicator shown while sending */}
          {sending && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{
                width: 26, height: 26, borderRadius: 8,
                background: '#E8A838',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 10, fontWeight: 800, color: '#1B2A4A',
              }}>
                AX
              </div>
              <div style={{
                padding: '10px 14px', borderRadius: '16px 16px 16px 4px',
                background: '#fff', border: '1px solid #e2e8f0',
                display: 'flex', gap: 4, alignItems: 'center',
              }}>
                {[0, 1, 2].map(i => (
                  <span key={i} style={{
                    width: 6, height: 6, borderRadius: '50%',
                    background: '#cbd5e1',
                    animation: `fcBounce 1.2s ease-in-out ${i * 0.2}s infinite`,
                    display: 'inline-block',
                  }} />
                ))}
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* ── Input bar ── */}
        {!loading && !error && (
          <div style={{
            padding: '10px 12px',
            borderTop: '1px solid #e5e7eb',
            display: 'flex',
            gap: 8,
            alignItems: 'center',
            background: '#fff',
            flexShrink: 0,
          }}>
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder="Type a message…"
              disabled={sending}
              style={{
                flex: 1,
                border: '1.5px solid #e5e7eb',
                borderRadius: 10,
                padding: '9px 13px',
                fontSize: 13,
                outline: 'none',
                color: '#1B2A4A',
                fontFamily: 'inherit',
                background: sending ? '#f8fafc' : '#fff',
                transition: 'border-color 0.15s',
              }}
              onFocus={e => (e.currentTarget.style.borderColor = '#E8A838')}
              onBlur={e => (e.currentTarget.style.borderColor = '#e5e7eb')}
            />
            <button
              onClick={sendMessage}
              disabled={sending || !input.trim()}
              style={{
                width: 38,
                height: 38,
                borderRadius: 10,
                border: 'none',
                background: sending || !input.trim()
                  ? '#f1f5f9'
                  : 'linear-gradient(135deg, #E8A838, #F5C563)',
                color: sending || !input.trim() ? '#94a3b8' : '#1B2A4A',
                cursor: sending || !input.trim() ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'all 0.15s',
                boxShadow: sending || !input.trim() ? 'none' : '0 2px 8px rgba(232,168,56,0.3)',
              }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* ─── Keyframe animations ─── */}
      <style>{`
        @keyframes fcSpin {
          to { transform: rotate(360deg); }
        }
        @keyframes fcBounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-5px); opacity: 1; }
        }
      `}</style>
    </>
  );
}
