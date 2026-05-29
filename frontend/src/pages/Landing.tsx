import React from 'react';
import { HeroSection } from '../components/Landing/HeroSection';
import { LoginForm } from '../components/Auth/LoginForm';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/Common/LoadingSpinner';

export const Landing: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) return <LoadingSpinner fullscreen />;

  return (
    <div style={{ padding: '40px 24px' }}>
      {user ? <HeroSection /> : <LoginForm />}
    </div>
  );
};
