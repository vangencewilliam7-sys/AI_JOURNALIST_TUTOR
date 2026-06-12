import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BrainCircuit, Play, Cpu, Eye, Target, Database, FileText, MessageSquare, GitBranch, Activity, Sparkles, CheckCircle, Loader2, User, Mic } from 'lucide-react';

const ScriptPage: React.FC = () => {
  const navigate = useNavigate();
  const [researchStep, setResearchStep] = useState(0);
  const [showFramework, setShowFramework] = useState(false);
  const [expandedThemes, setExpandedThemes] = useState<Set<number>>(new Set());
  const [expandedQuestions, setExpandedQuestions] = useState<Set<string>>(new Set());

  const [script, setScript] = useState<any>(null);
  const [themes, setThemes] = useState<any[]>([]);
  const [expertProfile, setExpertProfile] = useState<any>(null);

  useEffect(() => {
    let step = 1;
    setResearchStep(step);
    const interval = setInterval(() => {
      step++;
      setResearchStep(step);
      if (step === 4) {
        clearInterval(interval);

        setExpertProfile({
          expert_id: 'EXP-SRINI-001',
          name: 'Sreeni Rayaprolu',
          title: 'PWC Director',
          years: 20,
          domain: 'Oracle CPQ & CRM Architecture',
          archetype: 'Extreme Idealist / Highly Traditional Leader',
          persona_calibration: 'Deeply curious, high-respect, narrative-driven peer. Treats Sreeni as an extreme idealist who follows traditional philosophies.',
          context_brief: 'Handles massive sales system designs for clients like Tesla, Cisco, and Bank of America while maintaining a traditional lifestyle.',
        });

        setScript({
          opening_icebreaker: "Sreeni, welcome to the studio. Everyone in the industry knows you today as a powerhouse PWC Director managing massive sales system designs for companies like Bank of America and Tesla. But looking at where it all began, your path wasn't a straight line—you started with a BSc, spent years navigating heavy career struggles in a completely non-IT landscape, and fought your way in through Deloitte. Take me back to that foundational era: How did you originally get into this space, and what was the spark that kept you going through those initial struggles?",
          active_listening_cues: "Watch for transitions into his Deloitte era and his natural tendency to groom teams.",
          interview_arc: {
            phase_1_warmup: {
              phase_goal: "Warmup — Establish trust & open the narrative",
              questions: [
                { id: "Q1", question_text: "Take me back to that foundational era: How did you originally get into this space, and what was the spark that kept you going through those initial struggles?", rationale: "Opens his personal origin story. A BSc-to-PWC-Director arc is rich with hidden turning points and unspoken lessons." },
                { id: "Q2", question_text: "When you first entered the IT consulting world at Deloitte, what was the single hardest adjustment from your non-IT background?", rationale: "Extracts the tacit friction of a career pivot — the skills gap, the impostor syndrome, the survival strategies nobody writes about." }
              ]
            },
            phase_2_deep_dives: {
              phase_goal: "Deep Dive — Extract domain-specific tacit knowledge",
              questions: [
                { id: "Q3", question_text: "Walk me through your mental model when a client like Tesla comes to you and says 'We need CPQ.' How do you even begin to scope something that massive?", rationale: "Forces him to articulate the invisible decision framework he uses for scoping enterprise CPQ — the heuristics, the red flags, the gut checks." },
                { id: "Q4", question_text: "You manage custom configurations for electric cars, tractors, and data center networks. How do you handle the fact that Oracle CPQ requires continuous agility due to brutal quarterly software updates?", rationale: "Targets the pattern-break: most people think cloud software is set-and-forget. His reality is constant adaptation." }
              ]
            },
            phase_3_challenge: {
              phase_goal: "Challenge — Probe edge cases and contrarian views",
              questions: [
                { id: "Q5", question_text: "What is the most common mistake fresh engineers make when they first touch an Oracle CPQ implementation?", rationale: "Extracts 'anti-pattern' knowledge — the mistakes only an expert can name because textbooks don't cover them." }
              ]
            },
            phase_4_synthesis: {
              phase_goal: "Synthesis — Consolidate and close the narrative",
              questions: [
                { id: "Q6", question_text: "If you had to distill your 20 years into one sentence of advice for a PWC fresher joining your team on Monday, what would it be?", rationale: "Compression question — forces the expert to crystallize their deepest belief into a single actionable takeaway." }
              ]
            }
          }
        });

        setThemes([
          { theme_id: 1, theme_title: "Career Origins & The Non-IT Pivot", editorial_rationale: "His journey from BSc through career struggles to Deloitte and PWC Director — a rich, unspoken survival narrative." },
          { theme_id: 2, theme_title: "Enterprise CPQ Architecture", editorial_rationale: "Core domain expertise: scoping, configuring, and deploying Oracle CPQ for massive clients like Tesla and Cisco." },
          { theme_id: 3, theme_title: "Legacy-to-Cloud Migration Friction", editorial_rationale: "The hidden engineering pain of migrating from desktop Siebel CRM to Oracle CPQ Cloud under intense pressure." },
          { theme_id: 4, theme_title: "Team Grooming & Traditional Leadership", editorial_rationale: "His natural tendency to groom teams, rooted in his traditional idealist philosophy and deep personal values." }
        ]);
      }
    }, 1500);
    return () => clearInterval(interval);
  }, []);

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
      { id: 1, icon: Database, label: 'Loading Expert Profile — EXP-SRINI-001' },
      { id: 2, icon: Sparkles, label: 'Extracting Core Themes from Intake' },
      { id: 3, icon: FileText, label: 'Crafting Interview Script for Sreeni Rayaprolu' },
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
                  <h4>{t.theme_title}</h4>
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
                  <h4>{key.replace('phase_', 'Phase ').replace(/_/g, ' ')}</h4>
                  {phase.phase_goal && <small>{phase.phase_goal}</small>}
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
