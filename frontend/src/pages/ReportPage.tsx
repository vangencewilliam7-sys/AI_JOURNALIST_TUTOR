import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, Zap, BarChart3, Lightbulb, BookOpen, User, Target, FileText } from 'lucide-react';

const ReportPage: React.FC = () => {
  const navigate = useNavigate();
  const [knowledgeReport, setKnowledgeReport] = useState<any>(null);

  useEffect(() => {
    setKnowledgeReport({
      report_id: 'REP-DEMO-DAY1',
      report_title: "Enterprise Architecture — Tacit Knowledge Extraction",
      expert_name: 'Demo Expert',
      expert_title: 'Industry Leader',
      expert_domain: "Enterprise Architecture",
      knowledge_stream: 'General Expertise',
      interview_depth_score: 9.5,
      total_insights_extracted: 12,

      synthesis_blocks: [
        {
          block_title: "Personal Narrative Log",
          icon: "user",
          content: "The expert's path into their current role reveals a non-traditional progression, highlighting that deep technical mastery can be forged through operational pressure rather than formal education."
        },
        {
          block_title: "Tactical Domain Mechanics",
          icon: "target",
          content: "A core piece of tacit knowledge extracted is the expert's approach to custom configuration logic. They treat each client engagement as a ground-up architecture challenge rather than a template-driven rollout."
        },
        {
          block_title: "Pattern Breaks — What Conventional Wisdom Gets Wrong",
          icon: "zap",
          content: "The expert revealed a significant gap between industry perception and enterprise reality, emphasizing the need for continuous agility and re-validation in environments that are typically assumed to be static."
        }
      ]
    });
  }, []);

  if (!knowledgeReport) return <div>Loading...</div>;

  const r = knowledgeReport;

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'user': return <User size={18} />;
      case 'target': return <Target size={18} />;
      case 'zap': return <Zap size={18} />;
      default: return <FileText size={18} />;
    }
  };

  return (
    <div className="report-page" style={{ padding: '40px 20px', minHeight: '100vh', background: 'var(--bg)' }}>
      <div className="report-container" style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <button className="back-link" onClick={() => navigate('/interview')} style={{ margin: 0 }}>
            <ChevronRight size={14} style={{ transform: 'rotate(180deg)' }} /> Back to Interview
          </button>
          <button className="btn-go-live" onClick={() => navigate('/dashboard')}>
            Go to Homework Dashboard <ChevronRight size={16} />
          </button>
        </div>

        {/* Report Header */}
        <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '16px', padding: '32px', marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Zap size={14} style={{ color: 'var(--accent)' }} />
            <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Tacit Knowledge Report · {r.report_id}</span>
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, margin: '0 0 8px 0', lineHeight: '1.3' }}>{r.report_title}</h1>
          <p style={{ color: 'var(--text-dim)', fontSize: '14px', margin: '0 0 24px 0' }}>{r.expert_name} · {r.expert_title} · {r.knowledge_stream}</p>
          
          <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 16px', background: 'rgba(37, 99, 235, 0.05)', borderRadius: '10px', border: '1px solid rgba(37, 99, 235, 0.1)' }}>
              <BarChart3 size={18} style={{ color: 'var(--accent)' }} />
              <div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--accent)' }}>{r.interview_depth_score}/10</div>
                <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Extraction Quality</div>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 16px', background: 'rgba(37, 99, 235, 0.05)', borderRadius: '10px', border: '1px solid rgba(37, 99, 235, 0.1)' }}>
              <Lightbulb size={18} style={{ color: 'var(--accent)' }} />
              <div>
                <div style={{ fontSize: '20px', fontWeight: 800, color: 'var(--accent)' }}>{r.total_insights_extracted}</div>
                <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Insights Extracted</div>
              </div>
            </div>
          </div>
        </div>

        {/* Synthesis Blocks — Clean paragraph-based layout */}
        {r.synthesis_blocks.map((block: any, idx: number) => (
          <div key={idx} style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '12px', padding: '28px', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid var(--border)' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(37, 99, 235, 0.08)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {getIcon(block.icon)}
              </div>
              <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0 }}>{block.block_title}</h2>
            </div>
            <p style={{ fontSize: '14px', lineHeight: '1.8', color: 'var(--text-dim)', margin: 0 }}>
              {block.content}
            </p>
          </div>
        ))}

      </div>
    </div>
  );
};

export default ReportPage;
