import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { InterviewProvider } from './context/InterviewContext';
import { ErrorBoundary } from './components/Common/ErrorBoundary';
import { LoadingSpinner } from './components/Common/LoadingSpinner';

import { Landing } from './pages/Landing';
import { KnowledgeHub } from './pages/KnowledgeHub';
import { InterviewSetup } from './pages/InterviewSetup';
import { ScriptPreviewPage } from './pages/ScriptPreviewPage';
import { InterviewRoom } from './pages/InterviewRoom';
import { BlueprintReport } from './pages/BlueprintReport';

// Protected Route Wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();
  
  if (loading) return <LoadingSpinner fullscreen />;
  if (!user) return <Navigate to="/" replace />;
  
  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <InterviewProvider>
          <Router>
            <Routes>
              <Route path="/" element={<Landing />} />
              
              <Route path="/ingest" element={
                <ProtectedRoute>
                  <KnowledgeHub />
                </ProtectedRoute>
              } />
              
              <Route path="/setup" element={
                <ProtectedRoute>
                  <InterviewSetup />
                </ProtectedRoute>
              } />
              
              <Route path="/preview" element={
                <ProtectedRoute>
                  <ScriptPreviewPage />
                </ProtectedRoute>
              } />
              
              <Route path="/interview" element={
                <ProtectedRoute>
                  <InterviewRoom />
                </ProtectedRoute>
              } />
              
              <Route path="/report" element={
                <ProtectedRoute>
                  <BlueprintReport />
                </ProtectedRoute>
              } />
              
            </Routes>
          </Router>
        </InterviewProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App;
