import { useState, useCallback } from 'react';
import { api } from '../services/api';
import type { KnowledgeSource } from '../types';

export const useKnowledge = () => {
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSources = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/knowledge-sources');
      setSources(res.data.sources || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteSource = async (id: string) => {
    try {
      await api.delete(`/knowledge-sources/${id}`);
      setSources(prev => prev.filter(s => s.id !== id));
    } catch (err: any) {
      alert('Failed to delete source');
    }
  };

  const uploadDocuments = async (files: FileList | File[]) => {
    const formData = new FormData();
    Array.from(files).forEach(f => formData.append('files', f));

    const res = await api.post('/ingest-documents', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  };

  const ingestYoutube = async (url: string) => {
    const res = await api.post('/ingest-youtube', { url });
    return res.data;
  };

  return {
    sources,
    loading,
    error,
    fetchSources,
    deleteSource,
    uploadDocuments,
    ingestYoutube
  };
};
