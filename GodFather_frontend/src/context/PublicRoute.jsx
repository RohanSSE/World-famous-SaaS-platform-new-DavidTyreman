import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthProvider.jsx';

const PublicRoute = ({ children }) => {
  const { auth } = useAuth();

  // If authenticated, skip login/signup — go to Welcome (not user-dashboard / stepper)
  if (auth.isAuthenticated && !auth.loading) {
    const isAgency = auth.user?.role === 3 || auth.user?.role_name === "agency";
    return <Navigate to={isAgency ? "/agency-dashboard" : "/welcome"} replace />;
  }

  return children;
};

export default PublicRoute;
