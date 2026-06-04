import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import {
  Mic, MicOff, Send, BrainCircuit, ChevronRight, ShieldCheck,
  CloudDownload, Loader2, CheckCircle, Activity,
  FileText, Play, Sparkles, Cpu, Eye, Database, GitBranch, Target, MessageSquare,
  Upload, Trash2, AlertCircle, FolderOpen, Zap, BookOpen, Lightbulb, Crosshair,
  Swords, Route, HelpCircle, BarChart3, StopCircle, User
} from 'lucide-react';

interface Decision {
  action: string;
  internal_monologue: string;
  scripted_question_resolved?: boolean;
  tangent_detected?: {
    exists: boolean;
    topic: string | null;
  };
  bridge_suggestion?: string;
}

interface Message {
  id: string;
  role: 'expert' | 'ai';
  text: string;
  timestamp: number;
  decision?: Decision;
  script_progress?: string;
  chunks?: any[];
}

interface ScriptPhase {
  phase_goal: string;
  questions: any[];
}

interface InterviewScript {
  interview_arc: {
    phase_1_warmup: ScriptPhase;
    phase_2_deep_dives: ScriptPhase;
    phase_3_challenge: ScriptPhase;
    phase_4_synthesis: ScriptPhase;
  };
}

const API_BASE = import.meta.env.VITE_API_BASE || `http://${window.location.hostname}:8001`;

const App: React.FC = () => {
  const [view, setView] = useState<'landing' | 'research' | 'script_preview' | 'interview' | 'ingest' | 'report'>('landing');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [_isTranscribing, setIsTranscribing] = useState(false);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [researchStep, setResearchStep] = useState(0);
  const [tutorProfile, setTutorProfile] = useState({
    full_name: '',
    expertise_streams: '',
    years_of_experience: 0,
    short_bio: '',
    course_title: '',
    course_description: '',
    target_audience: '',
  });
  const [isSubmittingProfile, setIsSubmittingProfile] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [script, setScript] = useState<InterviewScript | null>(null);
  const [themes, setThemes] = useState<any[]>([]);
  const [openDecisionId, setOpenDecisionId] = useState<string | null>(null);
  const [expandedThemes, setExpandedThemes] = useState<Set<number>>(new Set());
  const [expandedQuestions, setExpandedQuestions] = useState<Set<string>>(new Set());
  const [showFramework, setShowFramework] = useState(false);
  const [scriptProgress, setScriptProgress] = useState<string>('0/0');
  const [knowledgeReport, setKnowledgeReport] = useState<any>(null);
  const [isSynthesizing, setIsSynthesizing] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const generateSessionId = () => {
    if (window.crypto?.randomUUID) {
      return window.crypto.randomUUID();
    }

    return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  };

  const [sessionId, setSessionId] = useState(() => generateSessionId());
  const [isStateRestored, setIsStateRestored] = useState(false);

  // Restore state on mount
  useEffect(() => {
    const saved = localStorage.getItem('ai_tutor_state');
    if (saved) {
      try {
        const p = JSON.parse(saved);
        if (p.view) setView(p.view);
        if (p.messages) setMessages(p.messages);
        if (p.tutorProfile) setTutorProfile(p.tutorProfile);
        if (p.script) setScript(p.script);
        if (p.themes) setThemes(p.themes);
        if (p.knowledgeReport) setKnowledgeReport(p.knowledgeReport);
        if (p.sessionId) setSessionId(p.sessionId);
        if (p.scriptProgress) setScriptProgress(p.scriptProgress);
      } catch (e) {
        console.error("Failed to restore state", e);
      }
    }
    setIsStateRestored(true);
  }, []);

  // Save state on change
  useEffect(() => {
    if (!isStateRestored) return;
    const stateToSave = {
      view, messages, tutorProfile, script, themes,
      knowledgeReport, sessionId, scriptProgress
    };
    localStorage.setItem('ai_tutor_state', JSON.stringify(stateToSave));
  }, [isStateRestored, view, messages, tutorProfile, script, themes, knowledgeReport, sessionId, scriptProgress]);

  const resetSession = () => {
    const newId = generateSessionId();
    setSessionId(newId);
    setMessages([]);
    setScript(null);
    setThemes([]);
    setScriptProgress('0/0');
    setShowFramework(false);
    setExpandedThemes(new Set());
    setExpandedQuestions(new Set());
    setOpenDecisionId(null);
    setKnowledgeReport(null);
    setView('landing');
    localStorage.removeItem('ai_tutor_state');
  };

  const handleSynthesizeKnowledge = async () => {
    setIsSynthesizing(true);
    try {
      const res = await axios.post(`${API_BASE}/synthesize-knowledge/${sessionId}`, {}, { timeout: 300000 });
      if (res.data.status === 'success') {
        setKnowledgeReport(res.data.report);
        setView('report');
      } else {
        alert('Synthesis failed: ' + (res.data.message || 'Unknown error'));
      }
    } catch (e: any) {
      console.error('Synthesis error:', e);
      alert('Failed to synthesize knowledge: ' + (e.response?.data?.detail || e.message));
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleEndInterview = async () => {
    if (!confirm('End the interview now? This will stop the session and extract tacit knowledge from what has been covered so far.')) return;
    setIsSynthesizing(true);
    try {
      const res = await axios.post(`${API_BASE}/end-interview/${sessionId}`, {}, { timeout: 300000 });
      if (res.data.report) {
        setKnowledgeReport(res.data.report);
        setView('report');
      } else {
        alert(res.data.message || 'Interview ended.');
        setView('landing');
      }
    } catch (e: any) {
      console.error('End interview error:', e);
      alert('Failed to end interview: ' + (e.response?.data?.detail || e.message));
    } finally {
      setIsSynthesizing(false);
    }
  };

  const downloadTranscript = () => {
    const header = `=== AI JOURNALIST — INTERVIEW TRANSCRIPT ===\nSession ID: ${sessionId}\nDate: ${new Date().toISOString().split('T')[0]}\nProgress: ${scriptProgress}\n${'='.repeat(50)}\n\n`;
    const body = messages.map((msg) => {
      const role = msg.role === 'expert' ? 'EXPERT' : 'AI JOURNALIST';
      const time = new Date(msg.timestamp).toLocaleTimeString();
      let entry = `[${time}] ${role}:\n${msg.text}\n`;
      if (msg.decision?.internal_monologue) {
        entry += `  >> Decision: ${msg.decision.internal_monologue}\n`;
      }
      return entry;
    }).join('\n---\n\n');
    const blob = new Blob([header + body], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `interview_${sessionId.slice(0, 8)}_${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadReport = () => {
    if (!knowledgeReport) return;
    const jsonStr = JSON.stringify(knowledgeReport, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `knowledge_report_${sessionId.slice(0, 8)}_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, openDecisionId]);

  useEffect(() => {
    if (view === 'interview' && messages.length === 0) handleSend('');
  }, [view]);

  const handlePrepareInterview = async () => {
    setView('research');
    setResearchStep(1);
    try {
      setTimeout(() => setResearchStep(2), 2000);
      setTimeout(() => setResearchStep(3), 4000);
      const response = await axios.post(`${API_BASE}/prepare-interview`, {
        user_session_id: sessionId,
      }, { timeout: 300000 });
      setScript(response.data.script);
      setThemes(response.data.themes);
      setResearchStep(4);
      setTimeout(() => setView('script_preview'), 1000);
    } catch (error: any) {
      console.error("Preparation error:", error);
      const detail = error?.response?.data?.detail || error?.message || 'Unknown error';
      alert(`Interview preparation failed: ${detail}\n\nPlease make sure the backend server is running on port 8001 and try again.`);
      setView('landing');
    }
  };

  const handleSend = async (text: string) => {
    if (!text.trim() && messages.length > 0) return;
    if (text.trim()) {
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'expert', text, timestamp: Date.now() }]);
    }
    setInputText('');
    setIsLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/generate-question`, {
        expert_answer: text,
        user_session_id: sessionId
      });
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        text: response.data.question,
        timestamp: Date.now(),
        decision: response.data.decision,
        script_progress: response.data.script_progress,
        chunks: response.data.chunks_used
      }]);
      setScriptProgress(response.data.script_progress || 'Reactive');
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'ai', text: "Error connecting to Knowledge Hub.", timestamp: Date.now() }]);
    } finally { setIsLoading(false); }
  };

  const toggleRecording = async () => {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const rec = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorderRef.current = rec;
        audioChunksRef.current = [];
        rec.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
        rec.onstop = async () => {
          stream.getTracks().forEach(t => t.stop());
          const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          if (blob.size < 1000) return;
          setIsTranscribing(true);
          try {
            const fd = new FormData();
            fd.append('audio', blob, 'recording.webm');
            const r = await axios.post(`${API_BASE}/transcribe`, fd);
            if (r.data.transcript?.trim()) handleSend(r.data.transcript.trim());
          } catch (err) { console.error(err); }
          finally { setIsTranscribing(false); }
        };
        rec.start();
        setIsRecording(true);
      } catch (err) { console.error(err); }
    } else {
      if (mediaRecorderRef.current?.state !== 'inactive') mediaRecorderRef.current?.stop();
      setIsRecording(false);
    }
  };



  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmittingProfile(true);
    try {
      await axios.post(`${API_BASE}/submit-tutor-profile`, {
        ...tutorProfile,
        expertise_streams: tutorProfile.expertise_streams.split(',').map(s => s.trim()),
        user_session_id: sessionId
      });
      setView('research');
      handlePrepareInterview();
    } catch (error) {
      console.error(error);
      alert('Failed to submit profile.');
    } finally {
      setIsSubmittingProfile(false);
    }
  };



  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setUploadFiles(prev => [...prev, ...Array.from(e.target.files!)]);
    }
  };

  if (view === 'landing') {
    return (
      <div className="landing">
        <nav className="landing-nav">
          <div className="landing-logo">
            <div className="landing-logo-icon"><BrainCircuit size={20} /></div>
            AI Journalist
          </div>
          <button className="btn-ghost" onClick={() => setView('tutor_setup')}>Tutor Setup</button>
          <button className="btn-ghost" onClick={resetSession}>+ New Session</button>
        </nav>
        <div className="landing-hero">

          <h1 className="landing-title">Extract Your<br />Unwritten Knowledge.</h1>
          <p className="landing-subtitle">Synthesizing expert tacit knowledge into a structured knowledge blueprint.</p>
          <button className="btn-primary" onClick={() => setView('tutor_setup')}>
            Start Setup <ChevronRight size={16} />
          </button>
        </div>
      </div>
    );
  }

  if (view === 'research') {
    const steps = [
      { id: 1, icon: Database, label: 'Scanning Knowledge Hub' },
      { id: 2, icon: Sparkles, label: 'Extracting Core Themes' },
      { id: 3, icon: FileText, label: 'Crafting Interview Script' },
    ];
    return (
      <div className="research-page">
        <div className="research-card">
          <h2>Editorial Research Scan</h2>
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

  if (view === 'script_preview') {
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

    const totalQuestions = Object.values(script?.interview_arc || {}).reduce(
      (sum: number, phase: any) => sum + (phase.questions?.length || 0), 0
    );

    return (
      <div className="script-page">
        <header className="script-header">
          <div className="script-header-left">
            <BrainCircuit size={22} style={{ color: 'var(--accent)' }} />
            <div><small>Research Complete</small><h1>Interview Blueprint</h1></div>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <button className="btn-ghost" onClick={() => setShowFramework(!showFramework)}>
              <Cpu size={14} style={{ marginRight: 4, verticalAlign: -2 }} />{showFramework ? 'Hide' : 'Show'} Framework
            </button>
            <button className="btn-go-live" onClick={() => setView('interview')}>
              {messages.length > 0 ? 'Return to Interview' : 'Launch Interview'} <Play size={16} />
            </button>
          </div>
        </header>

        {showFramework && (
          <div className="framework-banner">
            <h3><Cpu size={16} /> Script Generation Framework</h3>
            <div className="framework-stages">
              <div className="framework-stage">
                <div className="framework-stage-num">1</div>
                <div><strong>Research Scan</strong><p>Sampled 3 chunks per source (start, middle, end) across all knowledge sources → ~33 representative chunks</p></div>
              </div>
              <div className="framework-stage">
                <div className="framework-stage-num">2</div>
                <div><strong>Theme Extraction (LLM Call #1)</strong><p>Identified {themes.length} editorially compelling themes, each with emotional anchors and source evidence</p></div>
              </div>
              <div className="framework-stage">
                <div className="framework-stage-num">3</div>
                <div><strong>Script Crafting (LLM Call #2)</strong><p>Generated {totalQuestions} questions across 4 phases. Each question is grounded in a specific knowledge chunk with editorial reasoning.</p></div>
              </div>
            </div>
            <div className="framework-decision">
              <Activity size={14} /> <strong>Why this count?</strong> Each question targets ~3 min of conversation. {totalQuestions} × 3 = {totalQuestions * 3} min — optimal extraction window before expert fatigue.
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
                    {isOpen && (
                      <div className="theme-details">
                        {t.emotional_anchor && (
                          <div className="theme-detail-row">
                            <span className="theme-detail-label"><Target size={11} /> Emotional Anchor</span>
                            <span>{t.emotional_anchor}</span>
                          </div>
                        )}
                        {t.never_asked_angle && (
                          <div className="theme-detail-row">
                            <span className="theme-detail-label"><Sparkles size={11} /> Never-Asked Angle</span>
                            <span>{t.never_asked_angle}</span>
                          </div>
                        )}
                        {t.source_evidence?.length > 0 && (
                          <div className="theme-detail-row">
                            <span className="theme-detail-label"><Database size={11} /> Source Evidence</span>
                            <div className="theme-evidence-list">
                              {t.source_evidence.map((s: any, i: number) => (
                                <div key={i} className="evidence-chip">
                                  <strong>{s.source_title}</strong>
                                  <small>{s.chunk_preview}</small>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </aside>
            <div className="script-main">
              <div className="section-label"><div className="section-label-dot" /> Full Narrative Script ({totalQuestions} questions)</div>
              {Object.entries(script?.interview_arc || {}).map(([key, phase]: [string, any]) => (
                <div key={key} className="phase-block">
                  <div className="phase-header">
                    <h4>{key.replace('phase_', '').replace(/_/g, ' ')}</h4>
                    {phase.phase_goal && <small>{phase.phase_goal}</small>}
                  </div>
                  {phase.questions?.map((q: any) => {
                    const qId = q.question_id || `q-${Math.random()}`;
                    const isQOpen = expandedQuestions.has(qId);
                    return (
                      <div key={qId} className={`question-card ${isQOpen ? 'question-expanded' : ''}`}>
                        <div className="question-top-row">
                          <div className="question-id">{q.question_id}</div>
                          <div className="question-content"><p>"{q.question_text}"</p></div>
                        </div>
                        <button className="question-rationale-btn" onClick={() => toggleQuestion(qId)}>
                          <Eye size={11} /> {isQOpen ? 'Hide' : 'Why this question?'}
                        </button>
                        {isQOpen && (
                          <div className="question-rationale-panel">
                            {q.emotional_trigger && (
                              <div className="qr-item">
                                <span className="qr-label"><Target size={11} /> Emotional Trigger</span>
                                <span className="qr-value">{q.emotional_trigger}</span>
                              </div>
                            )}
                            {q.chunk_attribution && (
                              <>
                                <div className="qr-item">
                                  <span className="qr-label"><Database size={11} /> Source</span>
                                  <span className="qr-value">{q.chunk_attribution.source_title}</span>
                                </div>
                                {q.chunk_attribution.why_this_chunk && (
                                  <div className="qr-item qr-why">
                                    <span className="qr-label"><MessageSquare size={11} /> Editorial Reasoning</span>
                                    <p>{q.chunk_attribution.why_this_chunk}</p>
                                  </div>
                                )}
                                {q.chunk_attribution.chunk_content && (
                                  <div className="qr-item">
                                    <span className="qr-label"><FileText size={11} /> Chunk That Inspired This</span>
                                    <code className="qr-chunk">{q.chunk_attribution.chunk_content}</code>
                                  </div>
                                )}
                              </>
                            )}
                            {q.contingency && (
                              <div className="qr-item">
                                <span className="qr-label"><GitBranch size={11} /> Contingency (if short answer)</span>
                                <span className="qr-value qr-contingency">{q.contingency}</span>
                              </div>
                            )}
                            {q.estimated_minutes && (
                              <div className="qr-item">
                                <span className="qr-label"><Activity size={11} /> Estimated Time</span>
                                <span className="qr-value">~{q.estimated_minutes} min</span>
                              </div>
                            )}
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
  }

  if (view === 'tutor_setup') {
    return (
      <div className="ingest-page">
        <div className="ingest-container" style={{ maxWidth: '800px', width: '100%' }}>
          <button className="back-link" onClick={() => setView('landing')}>
            <ChevronRight size={14} style={{ transform: 'rotate(180deg)' }} /> Back to Home
          </button>
          <h2 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '4px' }}>
            <Database size={20} style={{ verticalAlign: '-3px', marginRight: '8px', color: 'var(--accent)' }} />
            Tutor Setup
          </h2>
          <p style={{ color: 'var(--text-dim)', fontSize: '13px', marginBottom: '32px' }}>Tell us about your expertise and the course you want to build.</p>

          <form onSubmit={handleProfileSubmit} className="setup-form">
            <div className="setup-grid">
              
              <div className="setup-col">
                <div className="setup-col-header">
                  <Database size={16} /> Tutor Identity
                </div>
                
                <div className="input-group">
                  <label>Full Name</label>
                  <input required placeholder="Jane Doe" className="input-field" value={tutorProfile.full_name} onChange={e => setTutorProfile({...tutorProfile, full_name: e.target.value})} />
                </div>

                <div className="input-group">
                  <label>Years of Experience</label>
                  <input required type="number" min="0" placeholder="5" className="input-field" value={tutorProfile.years_of_experience || ''} onChange={e => setTutorProfile({...tutorProfile, years_of_experience: parseInt(e.target.value) || 0})} />
                </div>

                <div className="input-group">
                  <label>Short Bio</label>
                  <textarea required placeholder="I have been building systems for..." className="input-field" style={{ minHeight: '120px' }} value={tutorProfile.short_bio} onChange={e => setTutorProfile({...tutorProfile, short_bio: e.target.value})} />
                </div>
              </div>

              <div className="setup-col">
                <div className="setup-col-header">
                  <Sparkles size={16} /> Course Blueprint
                </div>
                
                <div className="input-group">
                  <label>Course Title</label>
                  <input required placeholder="Advanced React Patterns" className="input-field" value={tutorProfile.course_title} onChange={e => setTutorProfile({...tutorProfile, course_title: e.target.value})} />
                </div>

                <div className="input-group">
                  <label>Target Audience</label>
                  <input required placeholder="Mid-level developers" className="input-field" value={tutorProfile.target_audience} onChange={e => setTutorProfile({...tutorProfile, target_audience: e.target.value})} />
                </div>

                <div className="input-group">
                  <label>Course Description / Syllabus Idea</label>
                  <textarea required placeholder="A deep dive into advanced patterns, focusing on..." className="input-field" style={{ minHeight: '120px' }} value={tutorProfile.course_description} onChange={e => setTutorProfile({...tutorProfile, course_description: e.target.value})} />
                </div>
              </div>

            </div>
            
            <div className="setup-full-width">
               <div className="input-group" style={{ marginBottom: 0 }}>
                  <label>Expertise Streams (comma separated)</label>
                  <input required placeholder="React, Node.js, System Design" className="input-field" value={tutorProfile.expertise_streams} onChange={e => setTutorProfile({...tutorProfile, expertise_streams: e.target.value})} />
               </div>
            </div>

            <button type="submit" className="btn-primary" disabled={isSubmittingProfile} style={{ marginTop: '24px', width: '100%', justifyContent: 'center' }}>
              {isSubmittingProfile ? <><Loader2 size={16} className="spin" /> Initializing...</> : 'Save & Generate Blueprint'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // ======= TACIT KNOWLEDGE REPORT VIEW =======
  if (view === 'report' && knowledgeReport) {
    const r = knowledgeReport;
    return (
      <div className="report-page">
        <div className="report-container">
          <button className="back-link" onClick={() => setView('interview')}>
            <ChevronRight size={14} style={{ transform: 'rotate(180deg)' }} /> Back to Interview
          </button>

          <button className="btn-ghost" onClick={downloadReport} style={{ marginBottom: '16px', marginLeft: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
            <CloudDownload size={14} /> Download Full Report (JSON)
          </button>

          {/* Report Header */}
          <div className="report-header">
            <div className="report-badge"><Zap size={12} /> TACIT KNOWLEDGE REPORT</div>
            <h1 className="report-title">{r.report_title || 'Knowledge Report'}</h1>
            <p className="report-domain">{r.expert_domain}</p>
            <div className="report-stats">
              <div className="report-stat">
                <BarChart3 size={16} />
                <div>
                  <span className="stat-number">{r.interview_depth_score}/10</span>
                  <span className="stat-label">Depth Score</span>
                </div>
              </div>
              <div className="report-stat">
                <Lightbulb size={16} />
                <div>
                  <span className="stat-number">{r.total_insights_extracted}</span>
                  <span className="stat-label">Insights</span>
                </div>
              </div>
              <div className="report-stat">
                <BookOpen size={16} />
                <div>
                  <span className="stat-number">{r.war_stories?.length || 0}</span>
                  <span className="stat-label">War Stories</span>
                </div>
              </div>
              <div className="report-stat">
                <Route size={16} />
                <div>
                  <span className="stat-number">{r.actionable_playbooks?.length || 0}</span>
                  <span className="stat-label">Playbooks</span>
                </div>
              </div>
            </div>
            <p className="report-summary">{r.summary}</p>
          </div>

          {/* Tutor Persona (Raw JSON) */}
          {r.tutor_persona && (
            <div className="report-section">
              <h2 className="section-title"><User size={18} /> Tutor Persona</h2>
              <div style={{ background: '#0f172a', borderRadius: '12px', padding: '20px', border: '1px solid #1e293b' }}>
                <div style={{ display: 'flex', gap: '20px', marginBottom: '20px', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: '280px' }}>
                    <h3 style={{ fontSize: '20px', color: '#fff', margin: '0 0 4px 0' }}>{r.tutor_persona.name}</h3>
                    <p style={{ color: '#818cf8', fontWeight: 'bold', fontSize: '14px', margin: 0 }}>{r.tutor_persona.headline}</p>
                    <p style={{ color: '#94a3b8', fontSize: '13px', marginTop: '8px' }}>{r.tutor_persona.years_of_experience} years of experience</p>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '10px' }}>
                      {r.tutor_persona.expertise_areas?.map((a: string, i: number) => (
                        <span key={i} style={{ background: '#1e293b', color: '#818cf8', padding: '3px 10px', borderRadius: '12px', fontSize: '11px' }}>{a}</span>
                      ))}
                    </div>
                  </div>
                  <div style={{ flex: 1, minWidth: '280px' }}>
                    <p style={{ margin: '0 0 6px 0' }}><strong style={{ color: '#e2e8f0' }}>Unique Angle:</strong> <span style={{ color: '#cbd5e1' }}>{r.tutor_persona.unique_angle}</span></p>
                    <p style={{ margin: '0 0 6px 0' }}><strong style={{ color: '#e2e8f0' }}>Teaching Style:</strong> <span style={{ color: '#cbd5e1' }}>{r.tutor_persona.teaching_style}</span></p>
                    {r.tutor_persona.credibility_markers?.length > 0 && (
                      <div style={{ marginTop: '8px' }}>
                        <strong style={{ color: '#e2e8f0', fontSize: '12px' }}>Credibility:</strong>
                        <ul style={{ paddingLeft: '16px', margin: '4px 0 0 0', color: '#94a3b8', fontSize: '12px' }}>
                          {r.tutor_persona.credibility_markers.map((c: string, i: number) => <li key={i}>{c}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
                {r.tutor_persona.linguistic_fingerprint && (
                  <div style={{ padding: '14px', background: '#1e293b', borderRadius: '8px', marginBottom: '16px' }}>
                    <strong style={{ color: '#818cf8', fontSize: '12px', textTransform: 'uppercase' }}>Linguistic Fingerprint</strong>
                    <p style={{ fontSize: '13px', marginTop: '6px', color: '#cbd5e1' }}><strong>Blueprint:</strong> {r.tutor_persona.linguistic_fingerprint.explanation_blueprint}</p>
                    <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '8px' }}>
                      {r.tutor_persona.linguistic_fingerprint.signature_phrases_or_metaphors?.map((p: string, i: number) => (
                        <span key={i} style={{ background: '#0f172a', color: '#a5b4fc', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontStyle: 'italic' }}>"{p}"</span>
                      ))}
                    </div>
                  </div>
                )}
                {r.tutor_persona.system_prompt && (
                  <div>
                    <strong style={{ color: '#818cf8', fontSize: '12px', textTransform: 'uppercase' }}>System Prompt (JSON)</strong>
                    <pre style={{ background: '#020617', color: '#a5f3fc', padding: '14px', borderRadius: '8px', fontSize: '12px', lineHeight: '1.5', overflow: 'auto', maxHeight: '300px', marginTop: '8px', whiteSpace: 'pre-wrap', wordBreak: 'break-word', border: '1px solid #1e293b' }}>
{JSON.stringify(r.tutor_persona, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Teaching Philosophy */}
          {r.teaching_philosophy && (
            <div className="report-section">
              <h2 className="section-title"><BrainCircuit size={18} /> Teaching Philosophy</h2>
              <div className="report-cards">
                <div className="report-card">
                  <strong>Core Beliefs</strong>
                  <ul style={{ paddingLeft: '16px', marginTop: '8px' }}>
                    {r.teaching_philosophy.core_beliefs?.map((b: string, i: number) => <li key={i}>{b}</li>)}
                  </ul>
                </div>
                <div className="report-card">
                  <strong>What Others Get Wrong</strong>
                  <ul style={{ paddingLeft: '16px', marginTop: '8px' }}>
                    {r.teaching_philosophy.what_others_get_wrong?.map((b: string, i: number) => <li key={i}>{b}</li>)}
                  </ul>
                </div>
                <div className="report-card">
                  <strong>Signature Methods</strong>
                  <ul style={{ paddingLeft: '16px', marginTop: '8px' }}>
                    {r.teaching_philosophy.signature_methods?.map((b: string, i: number) => <li key={i}>{b}</li>)}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Personal Journey */}
          {r.personal_journey && (
            <div className="report-section">
              <h2 className="section-title"><Route size={18} /> Personal Journey</h2>
              <div className="report-cards">
                <div className="report-card" style={{ gridColumn: '1 / -1' }}>
                  <p><strong>Origin Story:</strong> {r.personal_journey.origin_story}</p>
                  <p style={{ marginTop: '8px' }}><strong>Proudest Achievement:</strong> {r.personal_journey.proudest_achievement}</p>
                </div>
              </div>
            </div>
          )}

          {/* Course Blueprint Render (Coursera-Style) */}
          {r.course_structure?.modules && (
            <div className="report-section">
              <h2 className="section-title"><BookOpen size={18} /> Course Blueprint</h2>
              <div className="blueprint-meta" style={{marginBottom: '20px', padding: '16px', background: '#1e293b', borderRadius: '8px'}}>
                <h3 style={{ color: '#fff', fontSize: '18px', margin: '0 0 4px 0' }}>{r.course_structure.course_title}</h3>
                {r.course_structure.course_subtitle && <p style={{ color: '#94a3b8', fontSize: '13px', margin: '0 0 8px 0' }}>{r.course_structure.course_subtitle}</p>}
                <p style={{ margin: '4px 0' }}><strong style={{ color: '#e2e8f0' }}>Promise:</strong> <span style={{ color: '#cbd5e1' }}>{r.course_structure.transformation_promise}</span></p>
                {r.course_structure.target_audience && <p style={{ margin: '4px 0' }}><strong style={{ color: '#e2e8f0' }}>Audience:</strong> <span style={{ color: '#cbd5e1' }}>{r.course_structure.target_audience}</span></p>}
                {r.course_structure.estimated_duration && <p style={{ margin: '4px 0' }}><strong style={{ color: '#e2e8f0' }}>Duration:</strong> <span style={{ color: '#cbd5e1' }}>{r.course_structure.estimated_duration}</span></p>}
                <p style={{ margin: '4px 0' }}><strong style={{ color: '#e2e8f0' }}>Modules:</strong> <span style={{ color: '#818cf8', fontWeight: 'bold' }}>{r.course_structure.modules.length}</span> | <strong style={{ color: '#e2e8f0' }}>Total Topics:</strong> <span style={{ color: '#818cf8', fontWeight: 'bold' }}>{r.course_structure.modules.reduce((sum: number, m: any) => sum + (m.topics?.length || 0), 0)}</span></p>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {r.course_structure.modules.map((m: any, i: number) => (
                  <div key={i} style={{ background: '#0f172a', borderRadius: '10px', border: '1px solid #1e293b', overflow: 'hidden' }}>
                    <div style={{ padding: '16px 20px', borderBottom: '1px solid #1e293b', background: '#1e293b' }}>
                      <h3 style={{ fontSize: '16px', color: '#fff', margin: 0 }}>Module {i+1}: {m.module_title}</h3>
                      <p style={{ color: '#94a3b8', fontSize: '13px', margin: '4px 0 0 0' }}>{m.module_description}</p>
                      {m.learning_outcomes?.length > 0 && (
                        <div style={{ marginTop: '8px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                          {m.learning_outcomes.map((o: string, k: number) => (
                            <span key={k} style={{ background: '#0f172a', color: '#86efac', padding: '2px 8px', borderRadius: '4px', fontSize: '10px' }}>✓ {o}</span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div style={{ padding: '12px 20px' }}>
                      {m.topics?.map((t: any, j: number) => (
                        <div key={j} style={{ padding: '10px 0', borderBottom: j < (m.topics.length - 1) ? '1px solid #1e293b' : 'none', display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                          <span style={{ color: '#475569', fontWeight: 'bold', fontSize: '14px', minWidth: '24px' }}>{j+1}.</span>
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <strong style={{ color: '#e2e8f0', fontSize: '14px' }}>{t.topic_title}</strong>
                              <div style={{ display: 'flex', gap: '4px' }}>
                                {t.inferred && <span style={{ background: '#422006', color: '#fde047', padding: '2px 8px', borderRadius: '4px', fontSize: '10px', textTransform: 'uppercase' }}>inferred</span>}
                                {t.suggested_format && <span style={{ background: '#1e293b', color: '#818cf8', padding: '2px 8px', borderRadius: '4px', fontSize: '10px', textTransform: 'uppercase' }}>{t.suggested_format}</span>}
                              </div>
                            </div>
                            {t.key_concepts?.length > 0 && (
                              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '4px' }}>
                                {t.key_concepts.map((c: string, ci: number) => (
                                  <span key={ci} style={{ color: '#64748b', fontSize: '11px' }}>{ci > 0 ? '·' : ''} {c}</span>
                                ))}
                              </div>
                            )}
                            {t.tutor_insight && <p style={{ color: '#94a3b8', fontSize: '12px', margin: '4px 0 0 0', fontStyle: 'italic' }}>💡 {t.tutor_insight}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}


          {/* Structured Tacit Notes */}
          {r.tacit_insights?.length > 0 && (
            <div className="report-section">
              <h2 className="section-title"><Lightbulb size={18} /> Structured Tacit Notes</h2>
              {r.tacit_insights.map((themeGroup: any, index: number) => (
                <div key={index} style={{ marginBottom: '24px' }}>
                  <h3 className="note-theme-title">
                    {themeGroup.theme}
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {themeGroup.notes?.map((note: any, nIdx: number) => (
                      <div key={nIdx} className="note-card">
                        <div>
                          <span className="note-card-title">{note.note_title}</span>
                        </div>
                        <p className="note-card-content">{note.content}</p>
                        {note.expert_quote && (
                          <blockquote className="note-quote">
                            "{note.expert_quote}"
                          </blockquote>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}



          {/* Knowledge Gaps */}
          {r.knowledge_gaps?.length > 0 && (
            <div className="report-section">
              <h2 className="section-title"><HelpCircle size={18} /> Knowledge Gaps</h2>
              <div className="report-cards">
                {r.knowledge_gaps.map((item: any) => (
                  <div key={item.id} className="report-card gap-card">
                    <h3 className="gap-topic">{item.topic}</h3>
                    <p className="card-desc">{item.observation}</p>
                    <p className="card-followup"><strong>Suggested follow-up:</strong> {item.suggested_followup}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="chat-page">
      <header className="chat-header">
        <div className="chat-header-left">
          <button className="chat-logo-btn" onClick={() => setView('landing')}><BrainCircuit size={18} /></button>
          <div className="chat-header-info">
            <h1>Live Interview</h1>
            <span style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>{sessionId.slice(0, 8)}</span>
          </div>
        </div>
        <div className="chat-header-right">
          <button className="btn-stop" onClick={handleEndInterview} disabled={isSynthesizing} title="End interview and extract knowledge">
            {isSynthesizing ? <Loader2 size={14} className="spin" /> : <StopCircle size={14} />}
            <span>Stop Interview</span>
          </button>
          <button className="btn-synth" onClick={handleSynthesizeKnowledge} disabled={isSynthesizing} title="Generate Tacit Knowledge Report">
            {isSynthesizing ? <Loader2 size={14} className="spin" /> : <Zap size={14} />}
            <span>{isSynthesizing ? 'Synthesizing...' : 'Extract Knowledge'}</span>
          </button>
          <button className="btn-ghost" onClick={downloadTranscript} style={{ marginRight: '8px' }}>
            <CloudDownload size={14} style={{ marginRight: '4px', verticalAlign: '-2px' }} /> Download
          </button>
          <button className="btn-ghost" onClick={() => setView('script_preview')} style={{ marginRight: '12px' }}>
            <FileText size={14} style={{ marginRight: '4px', verticalAlign: '-2px' }} /> View Script
          </button>
          <div className="progress-section"><label>Progress</label><span>{scriptProgress}</span></div>
        </div>
      </header>

      <div className="chat-feed" ref={scrollRef}>
        {messages.map(msg => (
          <div key={msg.id} className={`msg ${msg.role === 'expert' ? 'msg-expert' : 'msg-ai'}`}>
            <div className="msg-bubble">
              {msg.role === 'ai' && <div className="msg-label"><span><ShieldCheck size={10} /> Grounded Follow-up</span></div>}
              <div className="msg-text">{msg.text}</div>
            </div>
            {msg.role === 'ai' && msg.decision && (
              <div className="decision-section">
                <button className="decision-toggle" onClick={() => setOpenDecisionId(openDecisionId === msg.id ? null : msg.id)}>
                  <Activity size={12} /> Decision Log
                </button>
                {openDecisionId === msg.id && (
                  <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl mt-2 text-xs">
                    <p className="text-indigo-400 font-bold mb-2">Internal Monologue:</p>
                    <p className="text-slate-300 italic mb-3">"{msg.decision.internal_monologue}"</p>
                    {msg.chunks && msg.chunks.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-slate-800">
                        <p className="text-emerald-500 font-bold mb-1">Source Context:</p>
                        <p className="text-slate-500">{msg.chunks[0].source_title}: {msg.chunks[0].content}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {isLoading && <div className="typing-indicator"><div className="typing-dots"><div className="typing-dot" /><div className="typing-dot" /><div className="typing-dot" /></div></div>}
      </div>

      <footer className="chat-input-bar">
        <div className="chat-input-wrapper">
          <button className={`mic-btn ${isRecording ? 'recording' : ''}`} onClick={toggleRecording}>
            {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
          </button>
          <input className="chat-textarea" placeholder="Speak or type your insight..." value={inputText} onChange={e => setInputText(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSend(inputText)} />
          <button className="send-btn" onClick={() => handleSend(inputText)}><Send size={20} /></button>
        </div>
      </footer>
    </div>
  );
};

export default App;
