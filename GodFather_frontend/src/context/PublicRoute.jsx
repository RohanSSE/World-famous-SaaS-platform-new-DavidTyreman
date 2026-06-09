import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthProvider.jsx';

const PublicRoute = ({ children }) => {
  const { auth } = useAuth();

  // If authenticated, skip login/signup — go to Welcome (not user-dashboard / stepper)
  if (auth.isAuthenticated && !auth.loading) {
    const isAdmin = auth.user?.is_superuser || auth.user?.is_staff || auth.user?.role_name === "admin";
    if (isAdmin) return <Navigate to="/admin" replace />;

    return <Navigate to="/welcome" replace />;
  }

  return children;
};

export default PublicRoute;
