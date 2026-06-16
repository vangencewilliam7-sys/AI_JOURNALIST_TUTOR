import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, MicOff, Send, HelpCircle, StopCircle, PauseCircle, Loader2, BrainCircuit, Eye, Target, Zap, FileText, ArrowRight } from 'lucide-react';

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

  const [showScriptSidebar, setShowScriptSidebar] = useState(true);
  const [scriptThemes, setScriptThemes] = useState<any[]>([]);
  const [activeBlock, setActiveBlock] = useState('Block 1: Personal Origin & Persona');
  const [tangentCount, setTangentCount] = useState(0);

  const sessionId = localStorage.getItem('session_id');
  const icebreakerData = JSON.parse(localStorage.getItem('icebreaker') || '{}');

  useEffect(() => {
    if (!sessionId) {
      navigate('/');
      return;
    }
    
    // Seed the conversation with a generic opening
    setMessages([
      {
        id: '1',
        role: 'ai',
        text: icebreakerData.opening_icebreaker || "Welcome to the studio. We're excited to dive into your background and extract the unwritten rules of your domain.",
        timestamp: Date.now() - 600000,
        decision: {
          intent_classification: 'opening_question',
          internal_reasoning: 'Day 1 opening icebreaker from the generated script.',
          action: 'script_question'
        }
      }
    ]);

    // Fetch the script data for the sidebar
    fetch(`http://localhost:9120/session/${sessionId}`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && data.session?.script) {
          const arc = data.session.script.interview_arc || data.session.script;
          const extractedThemes = Object.entries(arc || {}).map(([key, phase]: [string, any], idx) => ({
            theme_id: idx,
            theme_title: key.replace('block_', 'Block ').replace(/_/g, ' '),
            editorial_rationale: phase.goal || "Phase goal",
            tentative_duration: phase.tentative_duration_minutes || 20,
            questions: phase.questions || []
          }));
          setScriptThemes(extractedThemes);
          if (extractedThemes.length > 0) {
            setActiveBlock(extractedThemes[0].theme_title);
          }
        }
      })
      .catch(err => console.error("Failed to fetch session script", err));

  }, [sessionId, navigate]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const handleSend = async (text: string) => {
    if (!text.trim() || !sessionId) return;
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'expert', text, timestamp: Date.now() }]);
    setInputText('');
    setIsLoading(true);
    
    try {
      const res = await fetch('http://localhost:9120/live-turn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          expert_answer: text,
          current_script_question: "General exploration", // Ideally mapped to active UI question
          active_block: activeBlock,
          tangent_count: tangentCount
        })
      });
      const data = await res.json();
      
      const intent = data.decision?.intent || 'unknown';
      if (intent === 'substantive') {
        setTangentCount(prev => prev + 1);
      } else if (intent === 'skip' || data.decision?.action === 'next_script_question') {
        setTangentCount(0);
      }
      
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        text: data.question || "Let's move on to the next topic.",
        timestamp: Date.now(),
        decision: {
          intent_classification: data.decision?.intent || 'unknown',
          internal_reasoning: data.decision?.reasoning || 'Backend copilot decision',
          action: data.decision?.action || 'next'
        }
      }]);
    } catch (err) {
      console.error(err);
      alert("Failed to get AI response.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleEndInterview = async () => {
    if (!confirm('Pause the interview and run the Homework Engine?')) return;
    if (!sessionId) return;
    
    setIsSynthesizing(true);
    try {
      await fetch(`http://localhost:9120/end-session/${sessionId}`, { method: 'POST' });
      navigate('/homework');
    } catch (err) {
      console.error(err);
      alert("Failed to synthesize session.");
      setIsSynthesizing(false);
    }
  };

  const handleNextBlock = () => {
    const currentIndex = scriptThemes.findIndex(t => t.theme_title === activeBlock);
    if (currentIndex >= 0 && currentIndex < scriptThemes.length - 1) {
      setActiveBlock(scriptThemes[currentIndex + 1].theme_title);
      setTangentCount(0);
    }
  };

  if (isSynthesizing) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)', color: 'var(--text)' }}>
        <Loader2 size={48} className="spin" style={{ color: 'var(--accent)', marginBottom: '20px' }} />
        <h2>Synthesizing Knowledge...</h2>
        <p style={{ color: 'var(--text-dim)' }}>Extracting tacit knowledge from session SESS-DEMO-DAY1 for Demo Expert.</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', background: 'var(--bg)' }}>
      <div className="chat-page" style={{ flex: 1, position: 'relative', display: 'flex', flexDirection: 'column', height: '100%' }}>
      <header className="chat-header">
        <div className="chat-header-left">
          <button className="chat-logo-btn" onClick={() => setShowScriptSidebar(!showScriptSidebar)}>
            <BrainCircuit size={20} />
          </button>
          <div className="chat-header-info">
            <h1>Live Interview — Demo Expert</h1>
            <div className="chat-header-status">
              <div className="pulse-dot" style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--green)' }}></div>
              SESS-DEMO-DAY1 · Recording Active
            </div>
          </div>
        </div>
        
        <div className="chat-header-right" style={{ gap: '12px', display: 'flex', alignItems: 'center' }}>
          <div className="progress-section" style={{ marginRight: '16px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
            <label style={{ fontSize: '11px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Active Block: {activeBlock}</label>
            <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text)' }}>
              Tangent Depth: {tangentCount}
            </div>
          </div>
          
          <button className="btn-ghost" style={{ borderColor: 'var(--accent)', color: 'var(--accent)' }} onClick={handleNextBlock}>
            Next Block <ArrowRight size={14} style={{ marginLeft: '6px', verticalAlign: '-2px' }} />
          </button>
          <button className="btn-ghost" style={{ borderColor: 'var(--red)', color: 'var(--red)' }} onClick={handleEndInterview} disabled={isSynthesizing}>
            <PauseCircle size={14} style={{ marginRight: '6px', verticalAlign: '-2px' }} /> PAUSE INTERVIEW
          </button>
        </div>
      </header>

      <div className="chat-feed" ref={scrollRef}>
        {messages.map(m => (
          <div key={m.id} className={`msg msg-${m.role}`}>
            <div className="msg-label">
              {m.role === 'expert' ? 'Demo Expert' : 'AI Journalist'}
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

      {showScriptSidebar && (
        <div className="script-sidebar" style={{ width: '400px', height: '100%', background: 'var(--bg-card)', borderLeft: '1px solid var(--border)', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
          <div style={{ padding: '20px', borderBottom: '1px solid var(--border)', background: '#fff' }}>
            <h3 style={{ margin: 0, fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={16} style={{ color: 'var(--accent)' }}/> Live Teleprompter
            </h3>
            <p style={{ margin: '4px 0 0', fontSize: '12px', color: 'var(--text-dim)' }}>Read these questions to guide the interview.</p>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
            {scriptThemes.map(theme => (
              <div key={theme.theme_id} style={{ marginBottom: '24px' }}>
                <h4 style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-dim)', marginBottom: '12px', display: 'flex', justifyContent: 'space-between' }}>
                  <span>{theme.theme_title}</span>
                  <span style={{ color: 'var(--accent)', fontWeight: 'bold' }}>{theme.tentative_duration}m</span>
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {theme.questions.map((q: any) => (
                    <div key={q.id} style={{ background: '#f8fafc', border: '1px solid var(--border)', borderRadius: '8px', padding: '12px' }}>
                      <p style={{ margin: 0, fontSize: '13px', lineHeight: '1.5', fontWeight: 500 }}>"{q.question_text}"</p>
                      <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '8px', fontStyle: 'italic' }}>
                        Rationale: {q.rationale}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {scriptThemes.length === 0 && <p style={{ fontSize: '13px', color: 'var(--text-dim)' }}>Loading script...</p>}
          </div>
        </div>
      )}
    </div>
  );
};

export default InterviewPage;
