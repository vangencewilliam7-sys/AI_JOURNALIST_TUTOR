import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import ScriptPage from './pages/ScriptPage';
import InterviewPage from './pages/InterviewPage';
import ReportPage from './pages/ReportPage';
import HomeworkPage from './pages/HomeworkPage';
import { LoginPage } from './pages/LoginPage';
import { AuthProvider, useAuth } from './context/AuthContext';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { session } = useAuth();
  if (!session) return <Navigate to="/login" replace />;
  return <>{children}</>;
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          {/* Redirect root to landing. ProtectedRoute will bounce to login if not authenticated */}
          <Route path="/" element={<Navigate to="/landing" replace />} />
          
          <Route path="/landing" element={<ProtectedRoute><LandingPage /></ProtectedRoute>} />
          <Route path="/script" element={<ProtectedRoute><ScriptPage /></ProtectedRoute>} />
          <Route path="/interview" element={<ProtectedRoute><InterviewPage /></ProtectedRoute>} />
          <Route path="/report" element={<ProtectedRoute><ReportPage /></ProtectedRoute>} />
          <Route path="/homework" element={<ProtectedRoute><HomeworkPage /></ProtectedRoute>} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
