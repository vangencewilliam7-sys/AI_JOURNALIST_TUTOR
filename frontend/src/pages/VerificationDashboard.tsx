import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  CheckCircle, 
  Edit3, 
  Trash2, 
  Save, 
  AlertCircle, 
  ArrowRight,
  RotateCcw
} from 'lucide-react';

interface InsightItem {
  id: string;
  classification: string;
  title: string;
  content: string;
  expert_quote?: string;
  status: 'pending' | 'approved' | 'modified' | 'rejected';
}

const CLASSIFICATION_LABELS: Record<string, string> = {
  mental_model: 'Mental Model',
  heuristic: 'Heuristic',
  decision_rule: 'Decision Rule',
  failure_pattern: 'Failure Pattern',
  misconception: 'Misconception',
  tradeoff: 'Tradeoff',
  evaluation_signal: 'Evaluation Signal',
  constraint: 'Constraint',
  belief: 'Belief',
  turning_point: 'Turning Point',
  workflow: 'Workflow',
  tool_or_technology: 'Tool & Technology'
};

export default function VerificationDashboard() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [insights, setInsights] = useState<InsightItem[]>([]);
  const [activeTab, setActiveTab] = useState<string>('all');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState<string>('');
  const [editContent, setEditContent] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!sessionId) return;
    const token = localStorage.getItem('sb-access-token'); // Retrieve token if present

    fetch(`http://localhost:9120/insights/${sessionId}`, {
      headers: {
        'Authorization': `Bearer ${token || ''}`
      }
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          // Initialize status locally
          const initialized = data.insights.map((ins: any) => ({
            ...ins,
            status: ins.status || 'pending'
          }));
          setInsights(initialized);
        }
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Error fetching insights:', err);
        setIsLoading(false);
      });
  }, [sessionId]);

  const handleApprove = (id: string) => {
    setInsights(prev => prev.map(ins => 
      ins.id === id ? { ...ins, status: 'approved' } : ins
    ));
  };

  const handleReject = (id: string) => {
    setInsights(prev => prev.map(ins => 
      ins.id === id ? { ...ins, status: 'rejected' } : ins
    ));
  };

  const handleStartEdit = (item: InsightItem) => {
    setEditingId(item.id);
    setEditTitle(item.title);
    setEditContent(item.content);
  };

  const handleSaveEdit = (id: string) => {
    setInsights(prev => prev.map(ins => 
      ins.id === id ? { ...ins, title: editTitle, content: editContent, status: 'modified' } : ins
    ));
    setEditingId(null);
  };

  const handleReset = (id: string) => {
    // Re-fetches or resets status to pending
    setInsights(prev => prev.map(ins => 
      ins.id === id ? { ...ins, status: 'pending' } : ins
    ));
  };

  const handleSubmit = async () => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    const token = localStorage.getItem('sb-access-token');

    try {
      const res = await fetch('http://localhost:9120/insights/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token || ''}`
        },
        body: JSON.stringify({
          insights: insights.map(ins => ({
            id: ins.id,
            status: ins.status,
            title: ins.title,
            content: ins.content
          }))
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        alert('Tacit insights verified successfully!');
        navigate('/homework');
      } else {
        alert('Failed to submit verification.');
      }
    } catch (e) {
      console.error(e);
      alert('Network error submitting verifications.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Group insights by classification
  const categories = Array.from(new Set(insights.map(ins => ins.classification)));
  
  const filteredInsights = insights.filter(ins => {
    if (activeTab === 'all') return ins.status !== 'rejected';
    if (activeTab === 'rejected') return ins.status === 'rejected';
    return ins.classification === activeTab && ins.status !== 'rejected';
  });

  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)', color: 'var(--text)' }}>
        <div style={{ fontSize: '20px', fontWeight: 500, letterSpacing: '0.5px' }}>Synthesizing and Classifying Insights...</div>
        <div style={{ color: 'var(--text-dim)', fontSize: '14px', marginTop: '10px' }}>Extracting heuristics, workflows, and tools from your transcript.</div>
      </div>
    );
  }

  return (
    <div style={{ background: 'var(--bg)', color: 'var(--text)', minHeight: '100vh', padding: '40px 20px', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        
        {/* Header Section */}
        <header style={{ marginBottom: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: '28px', fontWeight: 700, margin: 0, color: 'var(--text)' }}>Tacit Knowledge Verification Dashboard</h1>
            <p style={{ color: 'var(--text-dim)', marginTop: '8px', fontSize: '15px' }}>
              We've synthesized your interview transcript into structured insights. Review, edit, or reject them before final course generation.
            </p>
          </div>
          <button 
            onClick={handleSubmit} 
            disabled={isSubmitting}
            style={{ 
              background: 'var(--accent, #7c6aff)', 
              color: '#fff', 
              border: 'none', 
              borderRadius: '8px', 
              padding: '12px 24px', 
              fontWeight: 600, 
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 14px rgba(124,106,255,0.4)',
              transition: 'transform 0.2s'
            }}
          >
            Submit Verification <ArrowRight size={16} />
          </button>
        </header>

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', paddingBottom: '12px', borderBottom: '1px solid var(--border, #333)', marginBottom: '32px' }}>
          <button 
            onClick={() => setActiveTab('all')}
            style={{
              padding: '8px 16px',
              borderRadius: '20px',
              border: 'none',
              background: activeTab === 'all' ? 'var(--accent, #7c6aff)' : 'rgba(255,255,255,0.05)',
              color: activeTab === 'all' ? '#fff' : 'var(--text-dim)',
              cursor: 'pointer',
              fontWeight: 500,
              whiteSpace: 'nowrap'
            }}
          >
            All Insights ({insights.filter(i => i.status !== 'rejected').length})
          </button>
          
          {categories.map(cat => (
            <button 
              key={cat}
              onClick={() => setActiveTab(cat)}
              style={{
                padding: '8px 16px',
                borderRadius: '20px',
                border: 'none',
                background: activeTab === cat ? 'var(--accent, #7c6aff)' : 'rgba(255,255,255,0.05)',
                color: activeTab === cat ? '#fff' : 'var(--text-dim)',
                cursor: 'pointer',
                fontWeight: 500,
                whiteSpace: 'nowrap'
              }}
            >
              {CLASSIFICATION_LABELS[cat] || cat} ({insights.filter(i => i.classification === cat && i.status !== 'rejected').length})
            </button>
          ))}

          <button 
            onClick={() => setActiveTab('rejected')}
            style={{
              padding: '8px 16px',
              borderRadius: '20px',
              border: 'none',
              background: activeTab === 'rejected' ? 'var(--red, #ef4444)' : 'rgba(255,255,255,0.05)',
              color: activeTab === 'rejected' ? '#fff' : 'var(--text-dim)',
              cursor: 'pointer',
              fontWeight: 500,
              whiteSpace: 'nowrap',
              marginLeft: 'auto'
            }}
          >
            Rejected ({insights.filter(i => i.status === 'rejected').length})
          </button>
        </div>

        {/* Empty State */}
        {filteredInsights.length === 0 && (
          <div style={{ textAlign: 'center', padding: '60px 20px', background: 'var(--bg-card, #1a1a1a)', borderRadius: '12px', border: '1px dashed var(--border, #333)' }}>
            <AlertCircle size={40} style={{ color: 'var(--text-dim)', marginBottom: '16px' }} />
            <h3 style={{ margin: 0, fontSize: '18px' }}>No insights in this category</h3>
            <p style={{ color: 'var(--text-dim)', marginTop: '8px' }}>All items have been approved or rejected.</p>
          </div>
        )}

        {/* Insights List */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
          {filteredInsights.map(item => {
            const isEditing = editingId === item.id;
            
            return (
              <div 
                key={item.id} 
                style={{ 
                  background: 'var(--bg-card, #1e1e1e)', 
                  border: `1px solid ${
                    item.status === 'approved' ? 'var(--green, #22c55e)' :
                    item.status === 'rejected' ? 'var(--red, #ef4444)' :
                    item.status === 'modified' ? 'var(--yellow, #eab308)' : 'var(--border, #333)'
                  }`,
                  borderRadius: '12px', 
                  padding: '24px', 
                  transition: 'all 0.2s',
                  position: 'relative'
                }}
              >
                
                {/* Upper Badge Line */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <span style={{ 
                    background: 'rgba(124,106,255,0.1)', 
                    color: 'var(--accent, #7c6aff)', 
                    padding: '4px 12px', 
                    borderRadius: '4px', 
                    fontSize: '12px', 
                    fontWeight: 600,
                    textTransform: 'uppercase'
                  }}>
                    {CLASSIFICATION_LABELS[item.classification] || item.classification}
                  </span>
                  
                  {/* Status Indicator */}
                  <span style={{ 
                    fontSize: '12px', 
                    fontWeight: 500,
                    color: 
                      item.status === 'approved' ? 'var(--green, #22c55e)' :
                      item.status === 'rejected' ? 'var(--red, #ef4444)' :
                      item.status === 'modified' ? 'var(--yellow, #eab308)' : 'var(--text-dim)'
                  }}>
                    {item.status.toUpperCase()}
                  </span>
                </div>

                {/* Edit Form / Content Display */}
                {isEditing ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <input 
                      type="text" 
                      value={editTitle} 
                      onChange={e => setEditTitle(e.target.value)}
                      style={{ 
                        background: 'rgba(0,0,0,0.2)', 
                        border: '1px solid var(--accent, #7c6aff)', 
                        color: 'var(--text)', 
                        borderRadius: '6px', 
                        padding: '10px', 
                        fontSize: '16px', 
                        fontWeight: 600 
                      }}
                    />
                    <textarea 
                      value={editContent} 
                      onChange={e => setEditContent(e.target.value)}
                      rows={4}
                      style={{ 
                        background: 'rgba(0,0,0,0.2)', 
                        border: '1px solid var(--accent, #7c6aff)', 
                        color: 'var(--text)', 
                        borderRadius: '6px', 
                        padding: '10px', 
                        fontSize: '14px', 
                        lineHeight: '1.5' 
                      }}
                    />
                  </div>
                ) : (
                  <div>
                    <h3 style={{ margin: '0 0 10px 0', fontSize: '18px', fontWeight: 600 }}>{item.title}</h3>
                    <p style={{ color: 'var(--text-dim, #ccc)', lineHeight: '1.6', fontSize: '14px', margin: 0 }}>
                      {item.content}
                    </p>
                    {item.expert_quote && (
                      <blockquote style={{ 
                        margin: '16px 0 0 0', 
                        paddingLeft: '12px', 
                        borderLeft: '3px solid var(--accent, #7c6aff)', 
                        color: 'rgba(255,255,255,0.4)', 
                        fontSize: '13px', 
                        fontStyle: 'italic' 
                      }}>
                        "{item.expert_quote}"
                      </blockquote>
                    )}
                  </div>
                )}

                {/* Action Buttons Footer */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '16px' }}>
                  {isEditing ? (
                    <>
                      <button 
                        onClick={() => handleSaveEdit(item.id)}
                        style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--green, #22c55e)', color: '#fff', border: 'none', borderRadius: '6px', padding: '8px 16px', fontSize: '13px', cursor: 'pointer' }}
                      >
                        <Save size={14} /> Save
                      </button>
                      <button 
                        onClick={() => setEditingId(null)}
                        style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text)', border: 'none', borderRadius: '6px', padding: '8px 16px', fontSize: '13px', cursor: 'pointer' }}
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      {item.status !== 'approved' && (
                        <button 
                          onClick={() => handleApprove(item.id)}
                          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(34,197,94,0.1)', color: 'var(--green, #22c55e)', border: '1px solid var(--green, #22c55e)', borderRadius: '6px', padding: '8px 16px', fontSize: '13px', cursor: 'pointer', transition: 'all 0.2s' }}
                        >
                          <CheckCircle size={14} /> Approve
                        </button>
                      )}
                      
                      <button 
                        onClick={() => handleStartEdit(item)}
                        style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(255,255,255,0.05)', color: 'var(--text)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', padding: '8px 16px', fontSize: '13px', cursor: 'pointer' }}
                      >
                        <Edit3 size={14} /> Modify
                      </button>

                      {item.status !== 'rejected' && (
                        <button 
                          onClick={() => handleReject(item.id)}
                          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(239,68,68,0.1)', color: 'var(--red, #ef4444)', border: '1px solid var(--red, #ef4444)', borderRadius: '6px', padding: '8px 16px', fontSize: '13px', cursor: 'pointer', transition: 'all 0.2s' }}
                        >
                          <Trash2 size={14} /> Reject
                        </button>
                      )}

                      {item.status !== 'pending' && (
                        <button 
                          onClick={() => handleReset(item.id)}
                          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(255,255,255,0.02)', color: 'var(--text-dim)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '6px', padding: '8px 16px', fontSize: '13px', cursor: 'pointer' }}
                        >
                          <RotateCcw size={14} /> Reset
                        </button>
                      )}
                    </>
                  )}
                </div>

              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
}
