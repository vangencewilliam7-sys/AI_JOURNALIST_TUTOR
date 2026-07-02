import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../supabaseClient';
import {
  ChevronRight,
  ChevronDown,
  BookOpen,
  Layers,
  Zap,
  Target,
  AlertTriangle,
  Lock,
  CheckSquare,
  GitBranch,
  XCircle,
  Lightbulb,
  BarChart3,
  ArrowLeft,
  Calendar,
  Cpu,
  Wrench
} from 'lucide-react';

// ── Types ──────────────────────────────────────────────────────────────────
interface KnowledgeNode {
  concept?: string;
  action_items?: string | string[];
  reference_guides?: string | string[];
  edge_cases?: string | string[];
  constraints?: string | string[];
  evaluation_path?: string | string[];
  common_mistakes?: string | string[];
  heuristics?: string | string[];
}

interface Topic {
  name: string;
  node?: KnowledgeNode;
  status?: string;
}

interface Module {
  name: string;
  module_context?: string;
  topics: Topic[];
}

interface KnowledgeReport {
  id: string;
  report_title: string;
  expert_domain: string;
  summary: string;
  interview_depth_score: number;
  total_insights_extracted: number;
  course_structure: any;
  tacit_insights: any[];
  created_at: string;
}

// ── Slot config ─────────────────────────────────────────────────────────────
const SLOTS = [
  { key: 'concept',          label: 'Concept',         icon: BookOpen,      color: '#6366f1' },
  { key: 'action_items',     label: 'Action Items',    icon: CheckSquare,   color: '#10b981' },
  { key: 'reference_guides', label: 'Reference Guides',icon: GitBranch,     color: '#f59e0b' },
  { key: 'edge_cases',       label: 'Edge Cases',      icon: AlertTriangle, color: '#ef4444' },
  { key: 'constraints',      label: 'Constraints',     icon: Lock,          color: '#8b5cf6' },
  { key: 'evaluation_path',  label: 'Evaluation Path', icon: Target,        color: '#06b6d4' },
  { key: 'common_mistakes',  label: 'Common Mistakes', icon: XCircle,       color: '#f97316' },
  { key: 'heuristics',       label: 'Heuristics',      icon: Lightbulb,     color: '#84cc16' },
];

// ── Helpers ──────────────────────────────────────────────────────────────────
function toArray(val: any): string[] {
  if (!val) return [];
  if (Array.isArray(val)) return val.filter(Boolean);
  if (typeof val === 'string' && val.trim()) return [val];
  return [];
}

function parseCourseStructure(raw: any): Module[] {
  if (!raw) return [];

  // If raw is an object with a modules array, extract and parse that
  if (raw && typeof raw === 'object' && !Array.isArray(raw) && Array.isArray(raw.modules)) {
    return parseCourseStructure(raw.modules);
  }

  // Already an array of modules
  if (Array.isArray(raw)) {
    return raw.map((m: any) => ({
      name: m.name || m.module || m.module_title || 'Unnamed Module',
      module_context: m.module_context || m.module_description || '',
      topics: (m.topics || []).map((t: any) => {
        if (typeof t === 'string') return { name: t };
        return {
          name: t.name || t.topic || t.topic_title || 'Unnamed Topic',
          node: t.node || t,
          status: t.status,
        };
      }),
    }));
  }

  // Object keyed by module name
  if (typeof raw === 'object') {
    return Object.entries(raw).map(([modName, topics]: [string, any]) => ({
      name: modName,
      topics: Array.isArray(topics)
        ? topics.map((t: any) => {
            if (typeof t === 'string') return { name: t };
            return { name: t.name || t.topic || t.topic_title || 'Unnamed Topic', node: t.node || t, status: t.status };
          })
        : [],
    }));
  }

  return [];
}

// ── Sub-components ───────────────────────────────────────────────────────────

const SlotBadge: React.FC<{ value: string }> = ({ value }) => (
  <div style={{
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '8px',
    padding: '8px 12px',
    fontSize: '13px',
    lineHeight: '1.6',
    color: 'var(--text-dim)',
  }}>
    {value}
  </div>
);

const KnowledgeSlot: React.FC<{ slotKey: string; label: string; icon: any; color: string; node: KnowledgeNode | undefined }> = ({
  slotKey, label, icon: Icon, color, node
}) => {
  const items = toArray((node as any)?.[slotKey]);
  if (items.length === 0) return null;

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: `1px solid ${color}22`,
      borderRadius: '10px',
      padding: '14px 16px',
      marginBottom: '10px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
        <div style={{
          width: '26px', height: '26px', borderRadius: '6px',
          background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={13} style={{ color }} />
        </div>
        <span style={{ fontSize: '11px', fontWeight: 700, color, textTransform: 'uppercase', letterSpacing: '0.07em' }}>
          {label}
        </span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {items.map((item, i) => <SlotBadge key={i} value={item} />)}
      </div>
    </div>
  );
};

const TopicCard: React.FC<{ topic: Topic; index: number }> = ({ topic, index }) => {
  const [open, setOpen] = useState(false);
  const hasNode = topic.node && Object.values(topic.node).some(v => toArray(v).length > 0);
  const isComplete = topic.status === 'COMPLETE' || topic.status === 'TOPIC_COMPLETE';

  return (
    <div style={{
      background: 'rgba(255,255,255,0.02)',
      border: '1px solid var(--border)',
      borderRadius: '10px',
      marginBottom: '8px',
      overflow: 'hidden',
      transition: 'border-color 0.2s',
    }}
      onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(99,102,241,0.3)')}
      onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
    >
      <button
        onClick={() => setOpen(!open)}
        disabled={!hasNode}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '12px 16px', background: 'transparent', border: 'none',
          cursor: hasNode ? 'pointer' : 'default', color: 'inherit', textAlign: 'left',
        }}
        id={`topic-${index}`}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{
            width: '20px', height: '20px', borderRadius: '50%',
            background: isComplete ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.05)',
            border: `1px solid ${isComplete ? '#10b981' : 'var(--border)'}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '9px', fontWeight: 700, color: isComplete ? '#10b981' : 'var(--text-muted)',
            flexShrink: 0,
          }}>
            {isComplete ? '✓' : index + 1}
          </span>
          <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text)' }}>{topic.name}</span>
          {topic.status && (
            <span style={{
              fontSize: '9px', fontWeight: 700,
              padding: '2px 8px', borderRadius: '20px',
              background: isComplete ? 'rgba(16,185,129,0.08)' : 'rgba(255,255,255,0.04)',
              color: isComplete ? '#10b981' : 'var(--text-muted)',
              border: `1px solid ${isComplete ? 'rgba(16,185,129,0.2)' : 'var(--border)'}`,
              textTransform: 'uppercase',
            }}>
              {topic.status}
            </span>
          )}
        </div>
        {hasNode && (
          <ChevronDown size={14} style={{
            color: 'var(--text-muted)', transition: 'transform 0.2s',
            transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
          }} />
        )}
      </button>

      {open && hasNode && (
        <div style={{ padding: '0 16px 16px 16px', borderTop: '1px solid var(--border)' }}>
          <div style={{ paddingTop: '14px' }}>
            {SLOTS.map(s => (
              <KnowledgeSlot key={s.key} slotKey={s.key} label={s.label} icon={s.icon} color={s.color} node={topic.node} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const ModuleAccordion: React.FC<{ module: Module; index: number }> = ({ module, index }) => {
  const [open, setOpen] = useState(index === 0);
  const completeCount = module.topics.filter(t => t.status === 'COMPLETE' || t.status === 'TOPIC_COMPLETE').length;
  const total = module.topics.length;
  const pct = total > 0 ? Math.round((completeCount / total) * 100) : 0;

  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: '14px', marginBottom: '16px', overflow: 'hidden',
    }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', padding: '20px 24px',
          background: 'transparent', border: 'none', cursor: 'pointer', color: 'inherit',
        }}
        id={`module-${index}`}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '36px', height: '36px', borderRadius: '10px',
            background: 'rgba(99,102,241,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Layers size={16} style={{ color: '#6366f1' }} />
          </div>
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text)' }}>{module.name}</div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
              {total} topic{total !== 1 ? 's' : ''} · {completeCount} complete
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          {total > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '60px', height: '4px', borderRadius: '4px', background: 'rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                <div style={{ width: `${pct}%`, height: '100%', background: '#6366f1', borderRadius: '4px', transition: 'width 0.4s' }} />
              </div>
              <span style={{ fontSize: '11px', fontWeight: 700, color: '#6366f1' }}>{pct}%</span>
            </div>
          )}
          <ChevronDown size={16} style={{
            color: 'var(--text-muted)', transition: 'transform 0.2s',
            transform: open ? 'rotate(180deg)' : 'rotate(0deg)',
          }} />
        </div>
      </button>

      {open && (
        <div style={{ padding: '0 20px 20px 20px', borderTop: '1px solid var(--border)' }}>
          {module.module_context && (
            <p style={{
              fontSize: '13.5px', lineHeight: '1.6', color: 'var(--text-dim)',
              background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)',
              borderRadius: '8px', padding: '12px 16px', margin: '16px 0 12px 0'
            }}>
              {module.module_context}
            </p>
          )}
          <div style={{ paddingTop: module.module_context ? '4px' : '16px' }}>
            {module.topics.length > 0
              ? module.topics.map((t, i) => <TopicCard key={i} topic={t} index={i} />)
              : <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>No topics extracted yet.</p>
            }
          </div>
        </div>
      )}
    </div>
  );
};

// ── Main Page ────────────────────────────────────────────────────────────────
const KnowledgeOutputPage: React.FC = () => {
  const navigate = useNavigate();
  const [reports, setReports] = useState<KnowledgeReport[]>([]);
  const [selected, setSelected] = useState<KnowledgeReport | null>(null);
  const [modules, setModules] = useState<Module[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const { data, error: err } = await supabase
          .from('tacit_knowledge_reports')
          .select('*')
          .order('created_at', { ascending: false });

        if (err) throw err;
        setReports(data || []);
        if (data && data.length > 0) {
          const r = data[0];
          setSelected(r);
          setModules(parseCourseStructure(r.course_structure));
        }
      } catch (e: any) {
        setError(e.message || 'Failed to load knowledge reports.');
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, []);

  const selectReport = (r: KnowledgeReport) => {
    setSelected(r);
    setModules(parseCourseStructure(r.course_structure));
  };

  if (loading) return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Loading knowledge reports…</div>
    </div>
  );

  if (error) return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ color: '#ef4444', fontSize: '14px' }}>{error}</div>
    </div>
  );

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', padding: '32px 20px', fontFamily: 'inherit' }}>
      <div style={{ maxWidth: '920px', margin: '0 auto' }}>

        {/* ── Top nav ── */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
          <button
            id="back-to-interview"
            onClick={() => navigate('/interview')}
            style={{
              display: 'flex', alignItems: 'center', gap: '6px',
              background: 'transparent', border: '1px solid var(--border)',
              borderRadius: '8px', padding: '8px 14px', cursor: 'pointer',
              color: 'var(--text-muted)', fontSize: '13px', fontWeight: 600,
            }}
          >
            <ArrowLeft size={14} /> Interview
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={14} style={{ color: 'var(--accent)' }} />
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Knowledge Output
            </span>
          </div>
        </div>

        {/* ── Report selector (if multiple) ── */}
        {reports.length > 1 && (
          <div style={{ display: 'flex', gap: '10px', marginBottom: '24px', flexWrap: 'wrap' }}>
            {reports.map(r => (
              <button
                key={r.id}
                onClick={() => selectReport(r)}
                style={{
                  padding: '8px 16px', borderRadius: '8px', fontSize: '12px', fontWeight: 600,
                  cursor: 'pointer', transition: 'all 0.15s',
                  background: selected?.id === r.id ? 'rgba(99,102,241,0.12)' : 'transparent',
                  border: `1px solid ${selected?.id === r.id ? '#6366f1' : 'var(--border)'}`,
                  color: selected?.id === r.id ? '#6366f1' : 'var(--text-muted)',
                }}
              >
                {r.report_title || r.expert_domain || 'Report'}
              </button>
            ))}
          </div>
        )}

        {reports.length === 0 && (
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: '14px', padding: '48px', textAlign: 'center',
          }}>
            <BookOpen size={32} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
            <h2 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 8px 0' }}>No Knowledge Reports Yet</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', margin: '0 0 24px 0' }}>
              Complete an interview session and synthesize the results to generate a knowledge report.
            </p>
            <button
              id="start-interview-cta"
              onClick={() => navigate('/interview')}
              className="btn-go-live"
            >
              Start Interview <ChevronRight size={14} />
            </button>
          </div>
        )}

        {selected && (
          <>
            {/* ── Report header ── */}
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: '16px', padding: '28px 32px', marginBottom: '28px',
            }}>
              <h1 style={{ fontSize: '22px', fontWeight: 800, margin: '0 0 6px 0', lineHeight: 1.3 }}>
                {selected.course_structure?.course_title || selected.report_title || selected.expert_domain || 'Knowledge Report'}
              </h1>
              <p style={{ color: 'var(--text-dim)', fontSize: '13px', margin: '0 0 16px 0' }}>
                {selected.expert_domain} · {new Date(selected.created_at).toLocaleDateString()}
              </p>

              {selected.course_structure?.course_context && (
                <div style={{ marginBottom: '20px', fontSize: '14px', lineHeight: '1.6', color: 'var(--text-dim)' }}>
                  {selected.course_structure.course_context}
                </div>
              )}

              <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  padding: '10px 16px', borderRadius: '10px',
                  background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.12)',
                }}>
                  <BarChart3 size={16} style={{ color: '#6366f1' }} />
                  <div>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: '#6366f1', lineHeight: 1 }}>
                      {selected.interview_depth_score ?? '—'}<span style={{ fontSize: '11px' }}>/10</span>
                    </div>
                    <div style={{ fontSize: '9px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Depth Score</div>
                  </div>
                </div>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  padding: '10px 16px', borderRadius: '10px',
                  background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.12)',
                }}>
                  <Lightbulb size={16} style={{ color: '#10b981' }} />
                  <div>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: '#10b981', lineHeight: 1 }}>
                      {selected.total_insights_extracted ?? '—'}
                    </div>
                    <div style={{ fontSize: '9px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Insights</div>
                  </div>
                </div>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  padding: '10px 16px', borderRadius: '10px',
                  background: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.12)',
                }}>
                  <Layers size={16} style={{ color: '#f59e0b' }} />
                  <div>
                    <div style={{ fontSize: '18px', fontWeight: 800, color: '#f59e0b', lineHeight: 1 }}>
                      {modules.length}
                    </div>
                    <div style={{ fontSize: '9px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Modules</div>
                  </div>
                </div>
                {selected.course_structure?.duration_weeks && (
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: '10px',
                    padding: '10px 16px', borderRadius: '10px',
                    background: 'rgba(139,92,246,0.06)', border: '1px solid rgba(139,92,246,0.12)',
                  }}>
                    <Calendar size={16} style={{ color: '#8b5cf6' }} />
                    <div>
                      <div style={{ fontSize: '18px', fontWeight: 800, color: '#8b5cf6', lineHeight: 1 }}>
                        {selected.course_structure.duration_weeks} <span style={{ fontSize: '11px' }}>wks</span>
                      </div>
                      <div style={{ fontSize: '9px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Duration</div>
                    </div>
                  </div>
                )}
              </div>

              {/* Tech Stack & Tools */}
              {(selected.course_structure?.tech_stack || selected.course_structure?.tools) && (
                <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px', borderTop: '1px solid var(--border)', paddingTop: '16px' }}>
                  {selected.course_structure?.tech_stack && selected.course_structure.tech_stack.length > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: 'var(--text-muted)', fontWeight: 600, minWidth: '95px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Cpu size={13} /> Tech Stack:
                      </span>
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {selected.course_structure.tech_stack.map((tech: string, idx: number) => (
                          <span key={idx} style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '2px 8px', fontSize: '12px', color: 'var(--text)' }}>
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  {selected.course_structure?.tools && selected.course_structure.tools.length > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: 'var(--text-muted)', fontWeight: 600, minWidth: '95px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Wrench size={13} /> Tools:
                      </span>
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {selected.course_structure.tools.map((tool: string, idx: number) => (
                          <span key={idx} style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', padding: '2px 8px', fontSize: '12px', color: 'var(--text-dim)' }}>
                            {tool}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}


              {selected.summary && (
                <p style={{
                  marginTop: '20px', fontSize: '14px', lineHeight: '1.7',
                  color: 'var(--text-dim)', borderTop: '1px solid var(--border)', paddingTop: '16px',
                }}>
                  {selected.summary}
                </p>
              )}
            </div>

            {/* ── Module → Topic → Knowledge Slots tree ── */}
            <div style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>
                Curriculum Map
              </span>
              <div style={{ flex: 1, height: '1px', background: 'var(--border)' }} />
            </div>

            {modules.length > 0
              ? modules.map((m, i) => <ModuleAccordion key={i} module={m} index={i} />)
              : (
                <div style={{
                  background: 'var(--bg-card)', border: '1px solid var(--border)',
                  borderRadius: '12px', padding: '32px', textAlign: 'center',
                }}>
                  <p style={{ color: 'var(--text-muted)', fontSize: '14px', margin: 0 }}>
                    Curriculum structure not yet extracted. Complete Block 3 (Curriculum Discovery) to populate modules and topics.
                  </p>
                </div>
              )
            }
          </>
        )}
      </div>
    </div>
  );
};

export default KnowledgeOutputPage;
