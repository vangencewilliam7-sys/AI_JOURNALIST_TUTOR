import React, { useCallback, useState } from 'react';
import { UploadCloud, FileType2, Loader2, Link } from 'lucide-react';

interface Props {
  onUpload: (files: FileList | File[]) => Promise<any>;
  onYoutube: (url: string) => Promise<any>;
}

export const FileUploader: React.FC<Props> = ({ onUpload, onYoutube }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [youtubeUrl, setYoutubeUrl] = useState('');

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length > 0) {
      setUploading(true);
      await onUpload(e.dataTransfer.files);
      setUploading(false);
    }
  }, [onUpload]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) {
      setUploading(true);
      await onUpload(e.target.files);
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleYoutubeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!youtubeUrl) return;
    setUploading(true);
    await onYoutube(youtubeUrl);
    setYoutubeUrl('');
    setUploading(false);
  };

  return (
    <div style={{ display: 'flex', gap: '20px', marginBottom: '48px' }}>
      <div 
        className="upload-zone"
        style={{
          flex: 1, border: `2px dashed ${isDragging ? '#6366f1' : '#334155'}`, borderRadius: '16px',
          padding: '40px', textAlign: 'center', background: isDragging ? 'rgba(99,102,241,0.05)' : 'transparent',
          transition: 'all 0.2s', position: 'relative'
        }}
        onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
      >
        <input 
          type="file" multiple accept=".pdf,.txt,.md,.csv,.docx"
          onChange={handleFileChange}
          style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer', width: '100%', height: '100%' }}
        />
        <UploadCloud size={32} style={{ color: isDragging ? '#6366f1' : '#64748b', margin: '0 auto 16px' }} />
        <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '8px' }}>Drag & Drop specific documents</h3>
        <p style={{ fontSize: '13px', color: '#64748b' }}>PDF, DOCX, TXT, MD • Max 50MB</p>
      </div>

      <div style={{ flex: 1, background: 'rgba(0,0,0,0.2)', borderRadius: '16px', padding: '24px', border: '1px solid #1e293b' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileType2 size={16} style={{ color: '#ef4444' }} /> Import YouTube Video
        </h3>
        <form onSubmit={handleYoutubeSubmit} style={{ display: 'flex', gap: '8px' }}>
          <div className="input-wrapper" style={{ flex: 1 }}>
            <Link size={16} className="input-icon" />
            <input 
              className="input-field" 
              placeholder="Paste YouTube URL..." 
              value={youtubeUrl}
              onChange={e => setYoutubeUrl(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-primary" style={{ padding: '0 20px' }} disabled={uploading || !youtubeUrl}>
            {uploading ? <Loader2 size={16} className="spin" /> : 'Import'}
          </button>
        </form>
      </div>
    </div>
  );
};
