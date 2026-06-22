import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { BrainCircuit, Play, Cpu, Eye, Target, Database, FileText, MessageSquare, GitBranch, Activity, Sparkles, CheckCircle, Loader2, User, Mic } from 'lucide-react';

const ScriptPage: React.FC = () => {
  const navigate = useNavigate();
  const { session } = useAuth();
  const [researchStep, setResearchStep] = useState(0);
  const [showFramework, setShowFramework] = useState(false);
  const [expandedThemes, setExpandedThemes] = useState<Set<number>>(new Set());
  const [expandedQuestions, setExpandedQuestions] = useState<Set<string>>(new Set());

  const [script, setScript] = useState<any>(null);
  const [themes, setThemes] = useState<any[]>([]);
  const [expertProfile, setExpertProfile] = useState<any>(null);

  const expertId = localStorage.getItem('expert_id');
  const icebreakerData = JSON.parse(localStorage.getItem('icebreaker') || '{}');

  useEffect(() => {
    if (!expertId) {
      navigate('/');
      return;
    }

    const generateScript = async () => {
      try {
        setResearchStep(1);
        await new Promise(r => setTimeout(r, 800));
        
        setResearchStep(2);
        const res = await fetch(`http://localhost:9120/generate-script`, { headers: { 'Authorization': `Bearer ${session?.access_token}` },
          method: 'POST'
        });
        const data = await res.json();
        
        setResearchStep(3);
        
        if (data.status === 'success') {
          setExpertProfile({
            name: data.expert?.name || 'Expert',
            domain: data.expert?.domain || 'Expertise Domain',
            years: data.expert?.years_of_experience || '?',
            title: data.expert?.current_title || '',
            persona_calibration: `Using calibrated dynamic archetype rules (${data.expert?.archetype || 'balanced'}).`
          });

          const arc = data.script.interview_arc || data.script;
          setScript({
            opening_icebreaker: icebreakerData.opening_icebreaker || "Welcome to the studio.",
            active_listening_cues: icebreakerData.active_listening_cues || "Listen carefully.",
            interview_arc: arc
          });

          // The current backend script generator focuses on phases rather than distinct themes, 
          // so we map phase goals to themes for the UI sidebar
          const extractedThemes = Object.entries(arc || {}).map(([key, phase]: [string, any], idx) => ({
            theme_id: idx,
            theme_title: key.replace('block_', 'Block ').replace(/_/g, ' '),
            editorial_rationale: phase.goal || "Phase goal",
            tentative_duration: phase.tentative_duration_minutes || 20,
            questions: phase.questions || []
          }));
          setThemes(extractedThemes);
          
          setTimeout(() => setResearchStep(4), 800);
        } else {
          console.error("Generation failed", data);
          alert("Failed to generate script.");
        }
      } catch (err) {
        console.error(err);
      }
    };

    generateScript();
  }, [expertId, navigate]);

  const toggleTheme = (id: number) => {
    setExpandedThemes(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleQuestion = (id: string) => {
    setExpandedQuestions(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  if (researchStep < 4) {
    const steps = [
      { id: 1, icon: Database, label: 'Loading Expert Profile — EXP-DEMO-001' },
      { id: 2, icon: Sparkles, label: 'Extracting Core Themes from Intake' },
      { id: 3, icon: FileText, label: 'Crafting Interview Script for Demo Expert' },
    ];
    return (
      <div className="research-page">
        <div className="research-card">
          <h2>Editorial Research Scan</h2>
          <p style={{ marginBottom: '24px' }}>Calibrating AI Journalist persona for Oracle CPQ domain...</p>
          <div className="research-steps">
            {steps.map(s => (
              <div key={s.id} className={`research-step ${researchStep >= s.id ? 'active' : ''}`}>
                <div className="research-step-icon"><s.icon size={18} /></div>
                <div className="research-step-text"><strong>{s.label}</strong></div>
                <div className="research-step-status">
                  {researchStep > s.id ? <CheckCircle size={18} /> : (researchStep === s.id && <Loader2 size={18} className="spin" />)}
                </div>
              </div>
            ))}
          </div>
          <div className="progress-bar"><div className="progress-bar-fill" style={{ width: `${(Math.min(researchStep, 3) / 3) * 100}%` }} /></div>
        </div>
      </div>
    );
  }

  const totalQuestions = Object.values(script?.interview_arc || {}).reduce(
    (sum: number, phase: any) => sum + (phase.questions?.length || 0), 0
  );

  return (
    <div className="script-page">
      <header className="script-header">
        <div className="script-header-left">
          <BrainCircuit size={22} style={{ color: 'var(--accent)' }} />
          <div><small>Research Complete — {expertProfile?.name}</small><h1>Interview Blueprint</h1></div>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button className="btn-ghost" onClick={() => setShowFramework(!showFramework)}>
            <Cpu size={14} style={{ marginRight: 4, verticalAlign: -2 }} />{showFramework ? 'Hide' : 'Show'} Framework
          </button>
          <button className="btn-go-live" onClick={() => navigate('/interview')}>
            Launch Interview <Play size={16} />
          </button>
        </div>
      </header>

      {/* Expert Profile Banner */}
      {expertProfile && (
        <div style={{ padding: '20px 48px', background: 'rgba(37, 99, 235, 0.04)', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', gap: '32px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'var(--accent)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><User size={22} /></div>
              <div>
                <strong style={{ fontSize: '15px' }}>{expertProfile.name}</strong>
                <div style={{ fontSize: '12px', color: 'var(--text-dim)' }}>{expertProfile.title} · {expertProfile.years} yrs · {expertProfile.domain}</div>
              </div>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-dim)', borderLeft: '1px solid var(--border)', paddingLeft: '20px' }}>
              <strong style={{ color: 'var(--accent)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Persona Calibration</strong>
              <p style={{ margin: '4px 0 0', maxWidth: '500px', lineHeight: '1.5' }}>{expertProfile.persona_calibration}</p>
            </div>
          </div>
        </div>
      )}

      {/* Opening Icebreaker */}
      {script?.opening_icebreaker && (
        <div style={{ padding: '24px 48px', background: 'var(--bg-card)', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Mic size={14} style={{ color: 'var(--accent)' }} />
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Opening Icebreaker — Read This Out Loud</span>
          </div>
          <blockquote style={{ margin: 0, padding: '16px 20px', background: 'rgba(37, 99, 235, 0.05)', border: '1px solid rgba(37, 99, 235, 0.15)', borderLeft: '3px solid var(--accent)', borderRadius: '8px', fontSize: '14px', lineHeight: '1.7', color: 'var(--text)', fontStyle: 'italic' }}>
            "{script.opening_icebreaker}"
          </blockquote>
          <div style={{ marginTop: '12px', padding: '10px 16px', background: 'rgba(22, 163, 74, 0.06)', border: '1px solid rgba(22, 163, 74, 0.15)', borderRadius: '8px', fontSize: '12px', color: 'var(--green)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Eye size={14} />
            <strong>Active Listening Cues:</strong> {script.active_listening_cues}
          </div>
        </div>
      )}

      {showFramework && (
        <div className="framework-banner">
          <h3><Cpu size={16} /> Script Generation Framework</h3>
          <div className="framework-stages">
            <div className="framework-stage">
              <div className="framework-stage-num">1</div>
              <div><strong>Research Scan</strong><p>Loaded profile for {expertProfile?.name} ({expertProfile?.domain})</p></div>
            </div>
            <div className="framework-stage">
              <div className="framework-stage-num">2</div>
              <div><strong>Theme Extraction (LLM Call #1)</strong><p>Identified {themes.length} editorially compelling themes</p></div>
            </div>
            <div className="framework-stage">
              <div className="framework-stage-num">3</div>
              <div><strong>Script Crafting (LLM Call #2)</strong><p>Generated {totalQuestions} questions across 4 phases.</p></div>
            </div>
          </div>
          <div className="framework-decision">
            <Activity size={14} /> <strong>Why this count?</strong> Each question targets ~3 min of conversation.
          </div>
        </div>
      )}

      <div className="script-body">
        <div className="script-layout">
          <aside className="script-sidebar">
            <div className="section-label"><div className="section-label-dot" /> Extracted Themes ({themes.length})</div>
            {themes.map((t: any) => {
              const isOpen = expandedThemes.has(t.theme_id);
              return (
                <div key={t.theme_id} className={`theme-card ${isOpen ? 'theme-expanded' : ''}`}>
                  <h4>{t.theme_title} <span style={{fontSize:'10px', marginLeft:'6px', color:'var(--accent)', fontWeight:'bold'}}>({t.tentative_duration}m)</span></h4>
                  <p>{t.editorial_rationale}</p>
                  <button className="theme-toggle" onClick={() => toggleTheme(t.theme_id)}>
                    <Eye size={11} /> {isOpen ? 'Hide' : 'Show'} Reasoning
                  </button>
                </div>
              );
            })}
          </aside>
          <div className="script-main">
            <div className="section-label"><div className="section-label-dot" /> Full Narrative Script ({totalQuestions} questions)</div>
            {Object.entries(script?.interview_arc || {}).map(([key, phase]: [string, any]) => (
              <div key={key} className="phase-block">
                <div className="phase-header">
                  <h4>{key.replace('block_', 'Block ').replace(/_/g, ' ')} <span style={{fontSize:'12px', marginLeft:'8px', color:'var(--accent)'}}>({phase.tentative_duration_minutes || 20}m)</span></h4>
                  {phase.goal && <small>{phase.goal}</small>}
                </div>
                {phase.questions?.map((q: any) => {
                  const qId = q.question_id || q.id;
                  const isQOpen = expandedQuestions.has(qId);
                  return (
                    <div key={qId} className={`question-card ${isQOpen ? 'question-expanded' : ''}`}>
                      <div className="question-top-row">
                        <div className="question-id">{qId}</div>
                        <div className="question-content"><p>"{q.question_text}"</p></div>
                      </div>
                      <button className="question-rationale-btn" onClick={() => toggleQuestion(qId)}>
                        <Eye size={11} /> {isQOpen ? 'Hide' : 'Why this question?'}
                      </button>
                      {isQOpen && (
                        <div className="question-rationale-panel">
                          <p>{q.rationale}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScriptPage;
