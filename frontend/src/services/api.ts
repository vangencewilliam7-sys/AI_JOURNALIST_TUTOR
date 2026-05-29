import axios from 'axios';
import { supabase } from './supabaseClient';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:9120';

// Create a centralized axios instance
export const api = axios.create({
  baseURL: API_URL,
});

// Request interceptor to attach JWT token
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession();
  
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }
  
  return config;
}, (error) => {
  return Promise.reject(error);
});

export const apiService = {
  async sendAudioMessage(sessionId: string, formData: FormData) {
    const response = await api.post(`/interview/${sessionId}/audio`, formData);
    return response.data;
  },

  async transcribeAudio(audioBlob: Blob) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.webm');
    const response = await api.post('/transcribe', formData);
    return response.data;
  },
};

// Response interceptor for generic error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // You could add global toast notifications here if desired
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);
