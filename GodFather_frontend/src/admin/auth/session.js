const AUTH_SESSION_KEY = "admin-auth-session";
function readFromStorage(storage) {
  const rawValue = storage.getItem(AUTH_SESSION_KEY);
  if (!rawValue) {
    return null;
  }
  try {
    return JSON.parse(rawValue);
  } catch {
    storage.removeItem(AUTH_SESSION_KEY);
    return null;
  }
}
function getAuthSession() {
  return readFromStorage(localStorage) ?? readFromStorage(sessionStorage);
}
function isAuthenticated() {
  return Boolean(getAuthSession());
}
function saveAuthSession(session) {
  const serializedSession = JSON.stringify(session);
  localStorage.setItem(AUTH_SESSION_KEY, serializedSession);
  sessionStorage.setItem(AUTH_SESSION_KEY, serializedSession);
}
function clearAuthSession() {
  localStorage.removeItem(AUTH_SESSION_KEY);
  sessionStorage.removeItem(AUTH_SESSION_KEY);
}
export {
  clearAuthSession,
  getAuthSession,
  isAuthenticated,
  saveAuthSession
};
