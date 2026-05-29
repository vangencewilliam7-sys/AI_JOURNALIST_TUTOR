import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { FileUploader } from '../components/Knowledge/FileUploader';
import { SourceList } from '../components/Knowledge/SourceList';
import { useKnowledge } from '../hooks/useKnowledge';

export const KnowledgeHub: React.FC = () => {
  const { sources, loading, fetchSources, uploadDocuments, ingestYoutube, deleteSource } = useKnowledge();

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  const handleUpload = async (files: FileList | File[]) => {
    await uploadDocuments(files);
    fetchSources();
  };

  const handleYoutube = async (url: string) => {
    await ingestYoutube(url);
    fetchSources();
  };

  return (
    <div className="layout-container">
      <nav className="landing-nav" style={{ marginBottom: '40px' }}>
        <Link to="/" className="btn-ghost" style={{ padding: '8px 16px' }}><ArrowLeft size={16} /> Back to Home</Link>
        <Link to="/setup" className="btn-primary" style={{ padding: '8px 16px' }}>Continue to Setup <ArrowRight size={16} /></Link>
      </nav>

      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 800, marginBottom: '8px' }}>Knowledge Hub</h1>
        <p style={{ color: 'var(--text-dim)', marginBottom: '40px' }}>
          Upload existing syllabi, notes, books, or YouTube videos. The AI will read and ground its questions in this material.
        </p>

        <FileUploader onUpload={handleUpload} onYoutube={handleYoutube} />
        
        <SourceList sources={sources} loading={loading} onDelete={deleteSource} />
      </div>
    </div>
  );
};
