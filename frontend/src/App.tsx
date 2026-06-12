import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import ScriptPage from './pages/ScriptPage';
import InterviewPage from './pages/InterviewPage';
import ReportPage from './pages/ReportPage';
import HomeworkPage from './pages/HomeworkPage';

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/script" element={<ScriptPage />} />
        <Route path="/interview" element={<InterviewPage />} />
        <Route path="/report" element={<ReportPage />} />
        <Route path="/dashboard" element={<HomeworkPage />} />
      </Routes>
    </Router>
  );
};

export default App;
