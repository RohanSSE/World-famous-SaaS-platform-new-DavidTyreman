import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthProvider.jsx';

const ProtectedRoute = ({ children }) => {
  const { auth } = useAuth();

  // If not authenticated, redirect to login
  if (!auth.isAuthenticated && !auth.loading) {
    return <Navigate to="/" replace />;
  }

  // If still loading auth state, show loading
  if (auth.loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: '#0B0D1F'
      }}>
        <div className="page-transition-spinner"></div>
      </div>
    );
  }

  return children;
};

export default ProtectedRoute;
