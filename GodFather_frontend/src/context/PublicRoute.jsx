import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthProvider.jsx';

const PublicRoute = ({ children }) => {
  const { auth } = useAuth();

  // If authenticated, redirect to chat interface
  if (auth.isAuthenticated && !auth.loading) {
    return <Navigate to="/user-dashboard" replace />;
  }

  return children;
};

export default PublicRoute;
