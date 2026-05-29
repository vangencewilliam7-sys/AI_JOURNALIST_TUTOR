import re

with open('c:/Users/vardh/OneDrive/Desktop/ai_journalist_tutor/frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports and Supabase Init
supabase_import = """import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';
const supabase = createClient(supabaseUrl, supabaseAnonKey);
"""
content = content.replace("import axios from 'axios';", "import axios from 'axios';\n" + supabase_import)

# 2. Add Auth States and logic
auth_state = """  const [user, setUser] = useState<any>(null);
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user || null);
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user || null);
    });
    return () => subscription.unsubscribe();
  }, []);

  useEffect(() => {
    if (user) {
      axios.defaults.headers.common['x-user-id'] = user.id;
    }
  }, [user]);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      if (authMode === 'signup') {
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        alert('Check your email to confirm, or login directly if auto-confirmed!');
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      }
    } catch (error: any) {
      alert(error.message);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSignOut = () => supabase.auth.signOut();
"""
content = content.replace("const [sessionId, setSessionId] = useState(() => generateSessionId());", "const [sessionId, setSessionId] = useState(() => generateSessionId());\n" + auth_state)

# 3. Handle unauthenticated render
unauth_render = """  if (!user) {
    return (
      <div className="landing" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', flexDirection: 'column' }}>
        <div style={{ background: '#1e293b', padding: '40px', borderRadius: '12px', width: '350px', textAlign: 'center' }}>
          <BrainCircuit size={48} style={{ color: '#818cf8', margin: '0 auto 20px' }} />
          <h2 style={{ marginBottom: '20px' }}>Course Architect</h2>
          <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required style={{ padding: '10px', borderRadius: '6px', border: '1px solid #334155', background: '#0f172a', color: '#fff' }} />
            <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required style={{ padding: '10px', borderRadius: '6px', border: '1px solid #334155', background: '#0f172a', color: '#fff' }} />
            <button type="submit" className="btn-primary" disabled={isLoading} style={{ justifyContent: 'center' }}>
              {isLoading ? <Loader2 className="spin" size={16} /> : (authMode === 'login' ? 'Sign In' : 'Sign Up')}
            </button>
          </form>
          <p style={{ marginTop: '20px', fontSize: '12px', color: '#94a3b8', cursor: 'pointer' }} onClick={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}>
            {authMode === 'login' ? "Don't have an account? Sign Up" : "Already have an account? Sign In"}
          </p>
        </div>
      </div>
    );
  }
"""
content = content.replace("  if (view === 'landing') {", unauth_render + "\n  if (view === 'landing') {")

# 4. Text Replacements
content = content.replace("AI Journalist", "Course Architect")
content = content.replace("Extract the<br />Unwritten Rules.", "Master Your<br />Course Blueprint.")
content = content.replace("Synthesizing expert tacit knowledge into structured intelligence.", "Synthesizing your raw knowledge into a highly detailed course syllabus.")
content = content.replace("Generate Tacit Knowledge Report", "Generate Course Blueprint")
content = content.replace("Extract Knowledge", "Generate Blueprint")
content = content.replace("AI JOURNALIST — INTERVIEW TRANSCRIPT", "COURSE ARCHITECT — BLUEPRINT TRANSCRIPT")
content = content.replace("AI JOURNALIST", "COURSE ARCHITECT")

# 5. Add Logout button to landing nav
content = content.replace("<button className=\"btn-ghost\" onClick={resetSession}>+ New Session</button>", "<button className=\"btn-ghost\" onClick={resetSession}>+ New Session</button>\n          <button className=\"btn-ghost\" onClick={handleSignOut} style={{ color: '#ef4444' }}>Sign Out</button>")

# 6. Report View Update
report_view_start = content.find("  // ======= TACIT KNOWLEDGE REPORT VIEW =======")
report_view_end = content.find("  return (\n    <div className=\"chat-page\">")

new_report_view = """  // ======= COURSE BLUEPRINT REPORT VIEW =======
  if (view === 'report' && knowledgeReport) {
    const r = knowledgeReport;
    return (
      <div className="report-page">
        <div className="report-container">
          <button className="back-link" onClick={() => setView('interview')}>
            <ChevronRight size={14} style={{ transform: 'rotate(180deg)' }} /> Back to Interview
          </button>

          {/* Report Header */}
          <div className="report-header">
            <div className="report-badge"><Zap size={12} /> COURSE BLUEPRINT</div>
            <h1 className="report-title">{r.course_title || 'Untitled Course'}</h1>
            <p className="report-domain"><strong>Target Audience:</strong> {r.target_audience}</p>
            <p className="report-summary" style={{ marginTop: '16px', fontStyle: 'italic' }}>{r.summary}</p>
            <div className="report-stats">
              <div className="report-stat">
                <BookOpen size={16} />
                <div>
                  <span className="stat-number">{r.total_modules || 0}</span>
                  <span className="stat-label">Modules</span>
                </div>
              </div>
            </div>
          </div>

          {/* Course Modules */}
          {r.course_modules?.length > 0 && (
            <div className="report-section">
              <h2 className="section-title"><Route size={18} /> Course Modules</h2>
              <div className="report-cards">
                {r.course_modules.map((mod: any, idx: number) => (
                  <div key={idx} className="report-card playbook-card">
                    <h3 className="playbook-title">Module {mod.module_number}: {mod.module_title}</h3>
                    <p className="card-context">{mod.description}</p>
                    
                    <div style={{ marginTop: '16px' }}>
                      <h4 style={{ fontSize: '13px', color: '#cbd5e1', marginBottom: '8px' }}>Lessons:</h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {mod.lessons?.map((lesson: any, i: number) => (
                          <div key={i} style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '6px' }}>
                            <strong style={{ display: 'block', color: '#818cf8', fontSize: '13px', marginBottom: '4px' }}>{lesson.lesson_title}</strong>
                            <p style={{ fontSize: '12px', color: '#94a3b8' }}>{lesson.details}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {mod.assignments_or_exercises?.length > 0 && (
                      <div style={{ marginTop: '16px', borderTop: '1px solid #334155', paddingTop: '12px' }}>
                        <h4 style={{ fontSize: '13px', color: '#cbd5e1', marginBottom: '8px' }}><Crosshair size={12} style={{ display: 'inline', marginRight: '4px' }} /> Exercises:</h4>
                        <ul className="playbook-steps">
                          {mod.assignments_or_exercises.map((ex: string, i: number) => (
                            <li key={i} style={{ fontSize: '12px' }}>{ex}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Marketing Hooks */}
          {r.marketing_hooks?.length > 0 && (
            <div className="report-section">
              <h2 className="section-title"><Target size={18} /> Marketing Hooks</h2>
              <div className="report-cards">
                {r.marketing_hooks.map((item: any, i: number) => (
                  <div key={i} className="report-card insight-card">
                    <blockquote className="card-quote">"{item.hook}"</blockquote>
                    <p className="card-why"><strong>Why it works:</strong> {item.why_it_works}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }
"""
content = content[:report_view_start] + new_report_view + content[report_view_end:]

with open('c:/Users/vardh/OneDrive/Desktop/ai_journalist_tutor/frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('App.tsx updated successfully.')
