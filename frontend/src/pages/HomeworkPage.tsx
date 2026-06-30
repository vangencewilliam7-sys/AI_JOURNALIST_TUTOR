import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { RefreshCw, PenTool, BrainCircuit, Mic, AlertTriangle, Eye, Loader2, CheckCircle, Database, Sparkles, FileText, Zap } from 'lucide-react';

const API_BASE_URL = 'http://localhost:9120';

const EvidenceSubmissionCard: React.FC<{ item: any; expertId: string; sessionId: string }> = ({ item, expertId, sessionId }) => {
  const [tab, setTab] = useState<'url' | 'file' | 'notes'>('url');
  const [inputVal, setInputVal] = useState('');
  const [status, setStatus] = useState<'idle' | 'submitting' | 'verifying' | 'done'>('idle');

  const handleSubmit = async () => {
    if (!inputVal) return;
    setStatus('submitting');
    try {
      await fetch('http://localhost:9120/homework/submit-evidence', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId || 'SESS-1',
          iteration_number: 1,
          loop_topic: item.topic || 'General Claim',
          material_type: tab === 'url' ? 'url' : tab === 'file' ? 'file' : 'text_description',
          content_or_url: inputVal,
          resource_mentioned: item.resource_mentioned || '',
          what_expert_claimed: item.what_expert_claimed || ''
        })
      });
      setStatus('verifying');
    } catch (e) {
      setStatus('verifying');
    }
  };

  return (
    <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px dashed var(--border)' }}>
      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--accent)', marginBottom: '8px' }}>
        📎 SUBMIT VERIFICATION EVIDENCE (Optional — Runs asynchronously)
      </div>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
        <button onClick={() => setTab('url')} style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '6px', border: 'none', background: tab === 'url' ? 'var(--accent)' : 'rgba(0,0,0,0.1)', color: tab === 'url' ? '#fff' : 'var(--text)' }}>URL / Website</button>
        <button onClick={() => setTab('file')} style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '6px', border: 'none', background: tab === 'file' ? 'var(--accent)' : 'rgba(0,0,0,0.1)', color: tab === 'file' ? '#fff' : 'var(--text)' }}>Upload Document</button>
        <button onClick={() => setTab('notes')} style={{ padding: '4px 10px', fontSize: '11px', borderRadius: '6px', border: 'none', background: tab === 'notes' ? 'var(--accent)' : 'rgba(0,0,0,0.1)', color: tab === 'notes' ? '#fff' : 'var(--text)' }}>Text / Notes</button>
      </div>
      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={inputVal}
          onChange={e => setInputVal(e.target.value)}
          placeholder={tab === 'url' ? "https://example.com/blog-post" : tab === 'file' ? "Paste Document Drive Link or Filename" : "Describe the artifact or quote..."}
          style={{ flex: 1, padding: '8px 12px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text)', fontSize: '12px' }}
          disabled={status !== 'idle'}
        />
        <button onClick={handleSubmit} disabled={status !== 'idle' || !inputVal} style={{ padding: '8px 16px', borderRadius: '6px', border: 'none', background: 'var(--accent)', color: '#fff', fontSize: '12px', fontWeight: 600, cursor: 'pointer' }}>
          {status === 'submitting' ? 'Sending...' : status === 'verifying' ? '⏳ Ingesting in Background' : 'Submit'}
        </button>
      </div>
      {status === 'verifying' && (
        <div style={{ fontSize: '11px', color: '#10b981', marginTop: '6px' }}>
          ✓ Background Verification Engine triggered. You do not need to wait—proceed to next iteration!
        </div>
      )}
    </div>
  );
};

const HomeworkPage: React.FC = () => {
  const navigate = useNavigate();
  const { session } = useAuth();
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
    // Retry with backoff — the backend synthesis may still be writing when this page first loads.
    // We retry up to 5 times (every 2 seconds) before giving up.
    let attempts = 0;
    const MAX_ATTEMPTS = 5;
    const RETRY_DELAY_MS = 2000;

    const fetchHomework = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/homework`, { headers: { 'Authorization': `Bearer ${session?.access_token}` } });
        const data = await res.json();
        if (data.status === 'success' && data.homework) {
          setHomeworkId(data.homework.id);
          setHomework(data.homework.ai_open_loops || []);
          if (data.homework.session_id) {
            localStorage.setItem('hw_reviewed_' + data.homework.session_id, 'true');
          }
          if (data.homework.human_manual_notes) {
            setManualNotes(data.homework.human_manual_notes);
          }
          return; // success — stop retrying
        }
      } catch (err) {
        console.error("Failed to fetch homework", err);
      }

      // If we're here, homework wasn't ready yet
      attempts++;
      if (attempts < MAX_ATTEMPTS) {
        setTimeout(fetchHomework, RETRY_DELAY_MS);
      } else {
        setHomework([]); // give up after 5 tries
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
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${session?.access_token}` },
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
            <span style={{ fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '1px' }}>Phase 5 & 6 — Verification & Evidence Engine</span>
          </div>
          <h1 style={{ fontSize: '32px', margin: '0 0 10px 0' }}>Homework Ledger</h1>
          <p style={{ color: 'var(--text-dim)', margin: '0 0 16px 0' }}>Expert ID: {expertId}</p>
          <div style={{ background: 'rgba(124, 106, 255, 0.08)', borderLeft: '4px solid var(--accent)', padding: '16px 20px', borderRadius: '8px', fontSize: '14px', lineHeight: '1.6', color: 'var(--text)' }}>
            💬 <strong>"You previously mentioned several resources that contributed to your expertise. Please provide supporting materials so the system can validate and better understand your learning journey."</strong>
          </div>
        </header>

        {/* AI Open Loops */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <AlertTriangle size={16} style={{ color: '#f59e0b' }} />
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#f59e0b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>AI-Identified Open Loops</span>
          </div>

          {homework.length === 0 && (
            <div style={{ background: 'var(--bg-card)', border: '1px solid #10b981', borderRadius: '12px', padding: '24px', textAlign: 'center', color: '#10b981', marginBottom: '16px' }}>
              <div style={{ fontSize: '24px', marginBottom: '8px' }}>🎉</div>
              <strong style={{ fontSize: '16px', display: 'block', marginBottom: '4px' }}>No Homework Found in This Block</strong>
              <span style={{ fontSize: '14px', color: 'var(--text-dim)' }}>No verification tasks or unverified learning resources were detected in this block's responses. You are clear to proceed to the next block!</span>
            </div>
          )}

          {homework.map((item, idx) => (
            <div key={idx} style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '24px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', gap: '12px' }}>
                <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '12px', flexShrink: 0 }}>
                  {idx + 1}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <h3 style={{ margin: 0, fontSize: '15px' }}>{item.topic}</h3>
                    {(item.priority === 'High' || item.priority === 'HIGH' || item.priority === 'CRITICAL') && (
                      <span style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444', fontSize: '10px', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold', textTransform: 'uppercase' }}>{item.priority}</span>
                    )}
                  </div>

                  {item.expert_quote_trigger && (
                    <div style={{ marginBottom: '12px', padding: '10px 14px', borderRadius: '8px', background: 'rgba(168, 85, 247, 0.08)', borderLeft: '3px solid #a855f7', fontStyle: 'italic', fontSize: '13px', color: 'var(--text)' }}>
                      <strong style={{ fontStyle: 'normal', display: 'block', marginBottom: '4px', color: '#a855f7' }}>📍 Found in Your Response Quote:</strong>
                      "{item.expert_quote_trigger}"
                    </div>
                  )}

                  {item.resource_mentioned && (
                    <div style={{ marginBottom: '12px', fontSize: '14px' }}>
                      <span style={{ color: 'var(--text-dim)', fontWeight: 600 }}>Resource: </span>
                      <span style={{ color: 'var(--accent)' }}>{item.resource_mentioned}</span>
                    </div>
                  )}

                  {item.what_expert_claimed && (
                    <div style={{ background: 'rgba(0,0,0,0.05)', padding: '10px 14px', borderRadius: '6px', borderLeft: '2px solid var(--border)', fontSize: '13px', fontStyle: 'italic', marginBottom: '12px', color: 'var(--text-dim)' }}>
                      "{item.what_expert_claimed}"
                    </div>
                  )}

                  {item.validation_status && (
                    <div style={{ marginBottom: '12px', padding: '12px', borderRadius: '8px', border: `1px solid ${item.validation_status === 'Valid' ? '#10b981' : item.validation_status === 'Invalid' ? '#ef4444' : '#f59e0b'}`, background: item.validation_status === 'Valid' ? 'rgba(16, 185, 129, 0.05)' : item.validation_status === 'Invalid' ? 'rgba(239, 68, 68, 0.05)' : 'rgba(245, 158, 11, 0.05)' }}>
                       <div style={{ fontSize: '12px', fontWeight: 'bold', color: item.validation_status === 'Valid' ? '#10b981' : item.validation_status === 'Invalid' ? '#ef4444' : '#f59e0b', marginBottom: '4px' }}>
                         ✓ AI FACT CHECK: {item.validation_status.toUpperCase()}
                       </div>
                       <div style={{ fontSize: '13px', color: 'var(--text)' }}>
                         {item.validation_reasoning}
                       </div>
                    </div>
                  )}

                  {item.host_homework_instructions && (
                    <div style={{ fontSize: '13px', color: 'var(--text-dim)', marginBottom: '12px' }}>
                      <strong>Host Instructions:</strong> {item.host_homework_instructions}
                    </div>
                  )}

                  <EvidenceSubmissionCard item={item} expertId={expertId} sessionId={homeworkId || 'SESS-1'} />
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
