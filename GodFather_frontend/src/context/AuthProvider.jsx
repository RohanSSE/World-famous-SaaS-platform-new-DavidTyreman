import React, { createContext, useState, useEffect, useContext, useCallback } from 'react';
import authService from '../services/authService';

const AuthContext = createContext({});
const AssistantContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [auth, setAuth] = useState({
    user: null,
    isAuthenticated: false,
    loading: true,
  });

  const [assistantState, setAssistantState] = useState({
    isOpen: false,
    step: 0,
    status: 'intro',
    messages: [
      {
        type: 'assistant',
        text: 'Hi! I am your assistant. I will guide you through the process.',
      },
    ],
    show: false,
    steps: [
      'Complete your profile',
      'Answer the foundation questions',
      'Review and submit your manifesto',
      'Explore your dashboard',
    ],
    userManuallyClosed: false, // Track if user manually closed the chat
  });

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const user = authService.getCurrentUser();
        const isAuthenticated = authService.isAuthenticated();

        setAuth({
          user,
          isAuthenticated,
          loading: false,
        });

        if (isAuthenticated) {
          setAssistantState(prev => ({ ...prev, show: true, isOpen: true }));
        } else {
          setAssistantState(prev => ({ ...prev, show: false }));
        }
      } catch (error) {
        setAuth({
          user: null,
          isAuthenticated: false,
          loading: false,
        });
        setAssistantState(prev => ({ ...prev, show: false }));
      }
    };

    checkAuth();
  }, []);

  const login = async (email, password) => {
    try {
      const data = await authService.login(email, password);
      setAuth({
        user: data.user || { email },
        isAuthenticated: true,
        loading: false,
      });
      setAssistantState(prev => ({ ...prev, show: true, isOpen: true }));
      return data;
    } catch (error) {
      throw error;
    }
  };

  const signup = async (email, password, confirmPassword, userType) => {
    try {
      const data = await authService.signup(email, password, confirmPassword, userType);
      // Don't auto-login after signup — user must log in manually
      // Remove any tokens that authService.signup may have stored
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      return data;
    } catch (error) {
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
      localStorage.clear();
      setAuth({
        user: null,
        isAuthenticated: false,
        loading: false,
      });
      setAssistantState(prev => ({ ...prev, show: false }));
    } catch (error) {
      console.error('Logout error:', error);
      localStorage.clear();
      setAuth({
        user: null,
        isAuthenticated: false,
        loading: false,
      });
      setAssistantState(prev => ({ ...prev, show: false }));
    }
  };

  const openChat = useCallback(() => {
    setAssistantState(prev => ({ ...prev, isOpen: true }));
  }, []);

  const closeChat = useCallback(() => {
    setAssistantState(prev => ({ ...prev, isOpen: false }));
  }, []);

  const setStep = useCallback((step) => {
    setAssistantState(prev => ({ ...prev, step }));
  }, []);

  const setStatus = useCallback((status) => {
    setAssistantState(prev => ({ ...prev, status }));
  }, []);

  const addMessage = useCallback((message) => {
    setAssistantState(prev => ({ ...prev, messages: [...prev.messages, message] }));
  }, []);

  return (
    <AuthContext.Provider value={{ auth, setAuth, login, signup, logout }}>
      <AssistantContext.Provider value={{ assistantState, openChat, closeChat, setStep, setStatus, addMessage }}>
        {children}
      </AssistantContext.Provider>
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const useAssistant = () => {
  const context = useContext(AssistantContext);
  if (!context) {
    throw new Error('useAssistant must be used within AuthProvider');
  }
  return context;
};
