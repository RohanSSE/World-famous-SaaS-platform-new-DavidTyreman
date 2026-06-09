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

function readCurrentUser() {
  const rawValue = localStorage.getItem("user");
  if (!rawValue) return null;
  try {
    return JSON.parse(rawValue);
  } catch {
    localStorage.removeItem("user");
    return null;
  }
}

function isAdminUser(user) {
  if (!user) return false;
  if (user.is_superuser || user.is_staff) return true;
  return (user.role_name || "").toLowerCase() === "admin";
}

function isAdminSession(session) {
  if (!session) return false;
  if (session.isAdmin === true || session.is_superuser || session.is_staff) return true;
  return (session.role || "").toLowerCase() === "admin";
}

function getAuthSession() {
  const session = readFromStorage(localStorage) ?? readFromStorage(sessionStorage);
  return isAdminSession(session) ? session : null;
}

function hasApiToken() {
  return Boolean(localStorage.getItem("accessToken"));
}

function isAuthenticated() {
  const hasAdminAccess = Boolean(getAuthSession() && hasApiToken() && isAdminUser(readCurrentUser()));
  if (!hasAdminAccess) {
    clearAdminAuthSession();
  }
  return hasAdminAccess;
}

function saveAuthSession(session) {
  const serializedSession = JSON.stringify({ ...session, isAdmin: true });
  localStorage.setItem(AUTH_SESSION_KEY, serializedSession);
  sessionStorage.setItem(AUTH_SESSION_KEY, serializedSession);
}

function clearAdminAuthSession() {
  localStorage.removeItem(AUTH_SESSION_KEY);
  sessionStorage.removeItem(AUTH_SESSION_KEY);
}

function clearAuthSession() {
  clearAdminAuthSession();
  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("user");
}
export {
  clearAdminAuthSession,
  clearAuthSession,
  getAuthSession,
  isAuthenticated,
  isAdminUser,
  saveAuthSession
};
