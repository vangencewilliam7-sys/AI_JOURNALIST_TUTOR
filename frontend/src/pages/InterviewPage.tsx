import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, MicOff, Send, HelpCircle, StopCircle, Loader2, BrainCircuit, Eye, Target, Zap } from 'lucide-react';

interface Message {
  id: string;
  role: 'expert' | 'ai';
  text: string;
  timestamp: number;
  decision?: {
    intent_classification: string;
    internal_reasoning: string;
    action: string;
  };
}

const InterviewPage: React.FC = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [showDecision, setShowDecision] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Seed the conversation with Sreeni's sample transcript
    setMessages([
      {
        id: '1',
        role: 'ai',
        text: "Sreeni, welcome to the studio. Take me back to that foundational era: How did you originally get into this space, and what was the spark that kept you going through those initial struggles?",
        timestamp: Date.now() - 600000,
        decision: {
          intent_classification: 'opening_question',
          internal_reasoning: 'Day 1 opening icebreaker from the generated script. Designed to unlock the personal origin narrative.',
          action: 'script_question'
        }
      },
      {
        id: '2',
        role: 'expert',
        text: "You know, it's interesting you ask that. Before I got into IT at all, I was managing a completely different world. My first real exposure to large-scale systems came when I was handling the heavy footprint desktop infrastructure for British Telecom. We were running Siebel CRM — the old, massive, on-premise desktop version. Everything was manual, everything was heavy. But that's where I learned configuration logic at its core. Then the pressure came to migrate everything to Oracle CPQ Cloud. And that migration... that was something else entirely. The legacy desktop rules were clashing with the new cloud architecture at every turn. We were dealing with brutal validation failures, data mapping nightmares. But that's what shaped my entire understanding of how CPQ actually works under the hood.",
        timestamp: Date.now() - 300000
      },
      {
        id: '3',
        role: 'ai',
        text: "How did you structure that cloud shift?",
        timestamp: Date.now() - 120000,
        decision: {
          intent_classification: 'substantive_pivot',
          internal_reasoning: 'Expert dropped a high-value transition story: legacy Siebel CRM → Oracle CPQ Cloud migration under intense pressure. This is a critical thread — he mentioned brutal validation failures and data mapping nightmares but hasn\'t unpacked the specific engineering decisions. Following the tangent before it disappears.',
          action: 'follow_tangent'
        }
      }
    ]);
  }, []);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const handleSend = async (text: string) => {
    if (!text.trim()) return;
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'expert', text, timestamp: Date.now() }]);
    setInputText('');
    setIsLoading(true);
    
    setTimeout(() => {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        text: "That's a powerful insight. When you say the validation rules 'clashed' — can you walk me through one specific scenario where a legacy desktop rule completely broke in the cloud environment?",
        timestamp: Date.now(),
        decision: {
          intent_classification: 'substantive_deep_dive',
          internal_reasoning: 'Expert is providing domain-specific operational detail about CPQ migration friction. Need to drill into a specific concrete example to extract actionable tacit knowledge rather than staying at the abstract level.',
          action: 'follow_tangent'
        }
      }]);
      setIsLoading(false);
    }, 1500);
  };

  const handleEndInterview = async () => {
    if (!confirm('End the interview and begin knowledge synthesis?')) return;
    setIsSynthesizing(true);
    setTimeout(() => {
      setIsSynthesizing(false);
      navigate('/report');
    }, 2500);
  };

  if (isSynthesizing) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)', color: 'var(--text)' }}>
        <Loader2 size={48} className="spin" style={{ color: 'var(--accent)', marginBottom: '20px' }} />
        <h2>Synthesizing Knowledge...</h2>
        <p style={{ color: 'var(--text-dim)' }}>Extracting tacit knowledge from session SESS-001-DAY1 for Sreeni Rayaprolu.</p>
      </div>
    );
  }

  return (
    <div className="chat-page">
      <header className="chat-header">
        <div className="chat-header-left">
          <button className="chat-logo-btn" onClick={() => navigate('/script')}>
            <BrainCircuit size={20} />
          </button>
          <div className="chat-header-info">
            <h1>Live Interview — Sreeni Rayaprolu</h1>
            <div className="chat-header-status">
              <div className="pulse-dot" style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--green)' }}></div>
              SESS-001-DAY1 · Recording Active
            </div>
          </div>
        </div>
        
        <div className="chat-header-right">
          <div className="progress-section">
            <label>Script Progress</label>
            <div className="progress-track">
              <div className="progress-track-bar">
                <div className="progress-track-fill" style={{ width: '33%' }}></div>
              </div>
              <span>2/6</span>
            </div>
          </div>
          <div className="session-badge">Oracle CPQ · Tutor Stream</div>
          <button className="btn-ghost" style={{ borderColor: 'var(--red)', color: 'var(--red)' }} onClick={handleEndInterview} disabled={isSynthesizing}>
            <StopCircle size={14} style={{ marginRight: '6px', verticalAlign: '-2px' }} /> END SESSION
          </button>
        </div>
      </header>

      <div className="chat-feed" ref={scrollRef}>
        {messages.map(m => (
          <div key={m.id} className={`msg msg-${m.role}`}>
            <div className="msg-label">
              {m.role === 'expert' ? 'Sreeni Rayaprolu' : 'AI Journalist'}
              {m.role === 'ai' && m.decision && (
                <button className="decision-toggle" onClick={() => setShowDecision(showDecision === m.id ? null : m.id)}>
                  <Zap size={10} /> AI Decision Log
                </button>
              )}
            </div>
            <div className="msg-bubble">
              <div className="msg-text">{m.text}</div>
            </div>
            {m.role === 'ai' && m.decision && showDecision === m.id && (
              <div className="decision-section">
                <div className="decision-panel">
                  <div className="decision-grid">
                    <div className="decision-item">
                      <div className="decision-item-label"><Target size={10} /> Intent Classification</div>
                      <div className="decision-item-value">
                        <span className={`depth-tag depth-deep`}>{m.decision.intent_classification}</span>
                      </div>
                    </div>
                    <div className="decision-item">
                      <div className="decision-item-label"><Zap size={10} /> Action</div>
                      <div className="decision-item-value">{m.decision.action}</div>
                    </div>
                  </div>
                  <div className="decision-monologue">
                    <div className="decision-item-label"><Eye size={10} /> Internal Reasoning</div>
                    <p style={{ fontSize: '13px', color: 'var(--text-dim)', lineHeight: '1.6', marginTop: '6px' }}>{m.decision.internal_reasoning}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="msg msg-ai">
            <div className="typing-indicator">
              <div className="typing-dots">
                <div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" />
              </div>
              <span className="typing-text">Synthesizing follow-up...</span>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input-bar">
        <div className="chat-input-wrapper">
          <button 
            className={`mic-btn ${isRecording ? 'recording' : ''}`} 
            onClick={() => setIsRecording(!isRecording)}
            disabled={isTranscribing}
          >
            {isTranscribing ? <Loader2 size={20} className="spin" /> : (isRecording ? <MicOff size={20} /> : <Mic size={20} />)}
          </button>
          <textarea
            value={inputText}
            onChange={e => setInputText(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(inputText); }
            }}
            placeholder="Type expert's response..."
            className="chat-textarea"
            rows={1}
          />
          <button className="send-btn" onClick={() => handleSend(inputText)} disabled={isLoading || !inputText.trim()}>
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default InterviewPage;
