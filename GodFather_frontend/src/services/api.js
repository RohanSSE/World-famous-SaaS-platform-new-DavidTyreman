import axios from 'axios';

const getDefaultApiBaseUrl = () => {
  if (typeof window === 'undefined') {
    return 'http://127.0.0.1:8001/api';
  }

  const { protocol, hostname } = window.location;
  const isLocalHost = ['localhost', '127.0.0.1', '0.0.0.0'].includes(hostname);

  if (isLocalHost) {
    return 'http://127.0.0.1:8001/api';
  }

  return `${protocol}//${hostname}:8001/api`;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || getDefaultApiBaseUrl();

const ADMIN_SESSION_KEY = 'admin-auth-session';

function clearStoredAuth() {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('user');
  localStorage.removeItem(ADMIN_SESSION_KEY);
  sessionStorage.removeItem(ADMIN_SESSION_KEY);
}

function getAuthRedirectPath() {
  return window.location.pathname.startsWith('/admin') ? '/admin/sign-in' : '/intro-ductory';
}

function redirectToAuth() {
  const nextPath = getAuthRedirectPath();
  if (window.location.pathname !== nextPath) {
    window.location.href = nextPath;
  }
}

function isAuthEndpoint(url = '') {
  return [
    '/auth/login/',
    '/auth/register/',
    '/auth/logout/',
    '/auth/password/',
    '/auth/token/refresh/',
    '/auth/token/verify/',
  ].some((path) => url.includes(path));
}
// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const isRefreshRequest = originalRequest?.url?.includes('/auth/token/refresh/');

    if (error.response?.status === 401 && isRefreshRequest) {
      clearStoredAuth();
      redirectToAuth();
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && isAuthEndpoint(originalRequest?.url)) {
      return Promise.reject(error);
    }

    // If 401 and haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
          clearStoredAuth();
          redirectToAuth();
          return Promise.reject(error);
        }
        const response = await api.post(`/auth/token/refresh/`, {
          refresh: refreshToken,
        });

        const { access } = response.data;
        localStorage.setItem('accessToken', access);

        originalRequest.headers.Authorization = `Bearer ${access}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        clearStoredAuth();
        redirectToAuth();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
