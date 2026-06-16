import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { RefreshCw, PenTool, BrainCircuit, Mic, AlertTriangle, Eye, Loader2, CheckCircle, Database, Sparkles, FileText, Zap } from 'lucide-react';

const API_BASE_URL = 'http://localhost:9120';

const HomeworkPage: React.FC = () => {
  const navigate = useNavigate();
  const [generationPhase, setGenerationPhase] = useState<'idle' | 'loading' | 'typing' | 'done'>('idle');
  const [loadingStep, setLoadingStep] = useState(0);
  const [typedText, setTypedText] = useState('');
  const typingRef = useRef<number | null>(null);

  const [homeworkId, setHomeworkId] = useState<string | null>(null);
  const [homework, setHomework] = useState<any[]>([]);
  const [manualNotes, setManualNotes] = useState('');
  const [flywheelScript, setFlywheelScript] = useState('');

  // Fallback if not set in local storage
  const expertId = localStorage.getItem('expert_id') || 'EXP-DEMO-001';

  useEffect(() => {
    const fetchHomework = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/homework/${expertId}`);
        const data = await res.json();
        if (data.status === 'success' && data.homework) {
          setHomeworkId(data.homework.id);
          setHomework(data.homework.ai_open_loops || []);
          if (data.homework.human_manual_notes) {
            setManualNotes(data.homework.human_manual_notes);
          }
        } else {
          setHomework([]);
        }
      } catch (err) {
        console.error("Failed to fetch homework", err);
      }
    };
    fetchHomework();
  }, [expertId]);

  const loadingSteps = [
    { icon: Database, label: 'Reading AI Open Loops from Homework Ledger...' },
    { icon: PenTool, label: 'Ingesting Journalist Manual Research Notes...' },
    { icon: Sparkles, label: 'Merging cliffhangers with human research...' },
    { icon: BrainCircuit, label: 'Generating Trust-Signal Opening Script...' },
    { icon: FileText, label: 'Crafting Day 2 Flywheel Bridge...' },
  ];

  const handleFlywheel = async () => {
    setGenerationPhase('loading');
    setLoadingStep(0);

    try {
      // 1. Save manual notes first
      if (homeworkId) {
        await fetch(`${API_BASE_URL}/homework/${homeworkId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ human_manual_notes: manualNotes })
        });
      }

      // 2. Trigger flywheel bridge & start next session
      const res = await fetch(`${API_BASE_URL}/start-session/${expertId}`, {
        method: 'POST'
      });
      const data = await res.json();
      
      if (data.status === 'success' && data.opener?.bridge_opener) {
        setFlywheelScript(data.opener.bridge_opener);
        if (data.session_id) {
          localStorage.setItem('session_id', data.session_id);
        }
      } else {
        setFlywheelScript("Welcome back. We had some great insights yesterday. Let's pick up where we left off.");
      }
    } catch (err) {
      console.error(err);
      setFlywheelScript("Welcome back. We had some great insights yesterday. Let's pick up where we left off.");
    }

    // UX Animation for the steps
    for (let i = 1; i <= loadingSteps.length; i++) {
      await new Promise(r => setTimeout(r, 1200));
      setLoadingStep(i);
    }
    
    setGenerationPhase('typing');
    setTypedText('');
  };

  // Typewriter effect
  useEffect(() => {
    if (generationPhase !== 'typing') return;
    let i = 0;
    const speed = 18; // ms per character
    const type = () => {
      if (i < flywheelScript.length) {
        setTypedText(flywheelScript.substring(0, i + 1));
        i++;
        typingRef.current = window.setTimeout(type, speed);
      } else {
        setGenerationPhase('done');
      }
    };
    type();
    return () => { if (typingRef.current) clearTimeout(typingRef.current); };
  }, [generationPhase, flywheelScript]);

  return (
    <div className="report-page" style={{ padding: '40px 20px', minHeight: '100vh', background: 'var(--bg)' }}>
      <div className="report-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
        
        <header style={{ marginBottom: '40px', borderBottom: '1px solid var(--border)', paddingBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent)', marginBottom: '8px' }}>
            <PenTool size={20} />
            <span style={{ fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '1px' }}>Phase 5 & 6 — Morning-After Preparation</span>
          </div>
          <h1 style={{ fontSize: '32px', margin: '0 0 10px 0' }}>Homework Ledger</h1>
          <p style={{ color: 'var(--text-dim)', margin: 0 }}>Expert ID: {expertId}</p>
        </header>

        {/* AI Open Loops */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <AlertTriangle size={16} style={{ color: '#f59e0b' }} />
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#f59e0b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>AI-Identified Open Loops</span>
          </div>

          {homework.length === 0 && (
            <p style={{ color: 'var(--text-dim)' }}>No open loops found for this expert yet. Complete a Day 1 session first.</p>
          )}

          {homework.map((item, idx) => (
            <div key={idx} style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '24px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', gap: '12px' }}>
                <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '12px', flexShrink: 0 }}>
                  {idx + 1}
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <h3 style={{ margin: 0, fontSize: '15px' }}>{item.topic}</h3>
                    {item.priority === 'High' && (
                      <span style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', fontSize: '10px', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>HIGH PRIORITY</span>
                    )}
                  </div>
                  <p style={{ color: 'var(--text-dim)', margin: '0 0 12px 0', fontSize: '14px', lineHeight: '1.7' }}>{item.reasoning}</p>
                  
                  {item.expert_quote_hook && (
                    <div style={{ background: 'rgba(0,0,0,0.05)', padding: '10px 14px', borderRadius: '6px', borderLeft: '2px solid var(--border)', fontSize: '13px', fontStyle: 'italic', marginBottom: '12px' }}>
                      "{item.expert_quote_hook}"
                    </div>
                  )}

                  <div style={{ fontSize: '13px', color: 'var(--accent)' }}>
                    <strong>Suggested Follow-up:</strong> {item.suggested_followup}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Human Manual Notes */}
        <div style={{ marginBottom: '40px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <PenTool size={16} style={{ color: 'var(--accent)' }} />
            <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Journalist Research Notes</span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginLeft: 'auto' }}>→ Saved to <code style={{ fontSize: '10px', background: 'rgba(0,0,0,0.05)', padding: '2px 6px', borderRadius: '4px' }}>human_manual_notes</code></span>
          </div>
          <textarea 
            value={manualNotes}
            onChange={(e) => setManualNotes(e.target.value)}
            placeholder="Add your overnight research here. Example: 'Found his old LinkedIn post about the British Telecom migration. He mentioned the validation engine had to be completely rewritten in 72 hours...'"
            style={{ width: '100%', minHeight: '140px', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '16px', color: 'var(--text)', fontSize: '14px', resize: 'vertical', lineHeight: '1.6' }}
            disabled={generationPhase !== 'idle'}
          />
        </div>

        {/* Flywheel Bridge */}
        {generationPhase === 'idle' && (
          <div style={{ background: 'linear-gradient(to right, rgba(37, 99, 235, 0.06), rgba(168, 85, 247, 0.06))', border: '1px solid var(--accent)', borderRadius: '12px', padding: '30px', textAlign: 'center', marginBottom: '32px' }}>
            <BrainCircuit size={32} style={{ color: 'var(--accent)', margin: '0 auto 16px auto' }} />
            <h2 style={{ margin: '0 0 10px 0', fontSize: '20px' }}>Ready for Day 2?</h2>
            <p style={{ color: 'var(--text-dim)', margin: '0 auto 24px auto', maxWidth: '500px', fontSize: '14px', lineHeight: '1.5' }}>
              The Flywheel Bridge will combine the AI's open loops with your manual research notes to generate a trust-signal opening script for Day 2.
            </p>
            <button 
              onClick={handleFlywheel}
              disabled={!homeworkId}
              style={{ background: homeworkId ? 'var(--accent)' : 'var(--border)', color: 'white', border: 'none', padding: '14px 28px', borderRadius: '8px', fontSize: '14px', fontWeight: 'bold', cursor: homeworkId ? 'pointer' : 'not-allowed', display: 'inline-flex', alignItems: 'center', gap: '8px' }}
            >
              <RefreshCw size={18} />
              Trigger Flywheel Bridge
            </button>
          </div>
        )}

        {/* Loading Animation */}
        {generationPhase === 'loading' && (
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '32px', marginBottom: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
              <Loader2 size={18} className="spin" style={{ color: 'var(--accent)' }} />
              <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--accent)' }}>Flywheel Bridge Processing...</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {loadingSteps.map((step, idx) => {
                const isActive = idx === loadingStep;
                const isDone = idx < loadingStep;
                const isPending = idx > loadingStep;
                return (
                  <div key={idx} style={{
                    display: 'flex', alignItems: 'center', gap: '14px',
                    padding: '14px 18px', borderRadius: '10px',
                    background: isDone ? 'rgba(22, 163, 74, 0.05)' : isActive ? 'rgba(37, 99, 235, 0.06)' : 'transparent',
                    border: `1px solid ${isDone ? 'rgba(22, 163, 74, 0.15)' : isActive ? 'rgba(37, 99, 235, 0.2)' : 'var(--border)'}`,
                    opacity: isPending ? 0.35 : 1,
                    transition: 'all 0.5s ease'
                  }}>
                    <div style={{
                      width: '36px', height: '36px', borderRadius: '10px',
                      background: isDone ? 'var(--green)' : isActive ? 'var(--accent)' : 'rgba(0,0,0,0.04)',
                      color: (isDone || isActive) ? 'white' : 'var(--text-muted)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                      transition: 'all 0.5s ease'
                    }}>
                      {isDone ? <CheckCircle size={18} /> : isActive ? <Loader2 size={18} className="spin" /> : <step.icon size={16} />}
                    </div>
                    <span style={{ fontSize: '13px', fontWeight: isDone || isActive ? 600 : 400, color: isDone ? 'var(--green)' : isActive ? 'var(--text)' : 'var(--text-muted)' }}>
                      {step.label}
                    </span>
                  </div>
                );
              })}
            </div>
            <div className="progress-bar" style={{ marginTop: '20px' }}>
              <div className="progress-bar-fill" style={{ width: `${(loadingStep / loadingSteps.length) * 100}%`, transition: 'width 1.2s ease' }} />
            </div>
          </div>
        )}

        {/* Typewriter Script Output */}
        {(generationPhase === 'typing' || generationPhase === 'done') && (
          <div style={{ background: 'var(--bg-card)', border: `2px solid ${generationPhase === 'done' ? 'var(--accent)' : 'rgba(37, 99, 235, 0.3)'}`, borderRadius: '12px', padding: '28px', marginBottom: '32px', transition: 'border-color 0.5s' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <Mic size={16} style={{ color: 'var(--accent)' }} />
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                {generationPhase === 'typing' ? 'Generating Day 2 Opening Script...' : 'Day 2 Opening Script — Read This Out Loud'}
              </span>
              {generationPhase === 'typing' && <Loader2 size={14} className="spin" style={{ color: 'var(--accent)', marginLeft: 'auto' }} />}
              {generationPhase === 'done' && <CheckCircle size={14} style={{ color: 'var(--green)', marginLeft: 'auto' }} />}
            </div>
            <blockquote style={{
              margin: 0, padding: '20px 24px',
              background: 'rgba(37, 99, 235, 0.04)',
              border: '1px solid rgba(37, 99, 235, 0.12)',
              borderLeft: '3px solid var(--accent)',
              borderRadius: '8px',
              fontSize: '14px', lineHeight: '1.8',
              color: 'var(--text)', fontStyle: 'italic',
              minHeight: '120px'
            }}>
              "{typedText}"
              {generationPhase === 'typing' && (
                <span style={{ display: 'inline-block', width: '2px', height: '16px', background: 'var(--accent)', marginLeft: '2px', verticalAlign: 'text-bottom', animation: 'blink 0.8s step-end infinite' }} />
              )}
            </blockquote>
            {generationPhase === 'done' && (
              <div style={{ marginTop: '20px', textAlign: 'center' }}>
                <button 
                  className="btn-go-live" 
                  onClick={() => navigate('/script')}
                  style={{ display: 'inline-flex' }}
                >
                  Launch Day 2 Session →
                </button>
              </div>
            )}
          </div>
        )}

      </div>

      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  );
};

export default HomeworkPage;
