import React, { useEffect, useRef } from 'react';
import { ShieldAlert, BookOpen, Loader2 } from 'lucide-react';
import { useInterviewContext } from '../context/InterviewContext';
import { useInterview } from '../hooks/useInterview';
import { ChatBubble } from '../components/Interview/ChatBubble';
import { ChatInput } from '../components/Interview/ChatInput';
import { PhaseBlock } from '../components/ScriptPreview/PhaseBlock';
import { ThemeCard } from '../components/ScriptPreview/ThemeCard';
import { useNavigate } from 'react-router-dom';

export const InterviewRoom: React.FC = () => {
  const { messages, script, scriptProgress } = useInterviewContext();
  const { handleSend, isLoading, handleEndInterview, isSynthesizing } = useInterview();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (!script) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h2>No Active Script</h2>
        <button className="btn-primary" onClick={() => navigate('/setup')} style={{ marginTop: '16px' }}>Go to Setup</button>
      </div>
    );
  }

  const arc = script.interview_arc;

  return (
    <div className="layout-container interview-layout">
      <div className="app-grid">
        
        {/* Left Sidebar - Chat */}
        <div className="chat-container">
          <header className="chat-header">
            <div>
              <h2 style={{ fontSize: '15px', fontWeight: 800 }}>Extraction Room</h2>
              <p style={{ fontSize: '12px', color: 'var(--text-dim)' }}>Script Progress: {scriptProgress}</p>
            </div>
            <button className="btn-primary" onClick={handleEndInterview} disabled={isSynthesizing} style={{ padding: '6px 12px', fontSize: '12px' }}>
              {isSynthesizing ? <Loader2 size={12} className="spin" /> : 'End & Synthesize'}
            </button>
          </header>
          
          <div className="chat-messages">
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', marginTop: '100px', color: 'var(--text-dim)' }}>
                <ShieldAlert size={48} style={{ opacity: 0.2, margin: '0 auto 16px' }} />
                <h3>Waiting for AI...</h3>
              </div>
            )}
            
            {messages.map((msg) => (
              <ChatBubble key={msg.id} msg={msg} />
            ))}
            
            {isLoading && (
              <div className="msg msg-ai">
                <div className="msg-bubble" style={{ background: 'transparent', border: 'none' }}>
                  <Loader2 size={16} className="spin" style={{ color: 'var(--accent)' }} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <ChatInput onSend={handleSend} disabled={isLoading || isSynthesizing} />
        </div>
      </div>
    </div>
  );
};
