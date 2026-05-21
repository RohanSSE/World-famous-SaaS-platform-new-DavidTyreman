export type AuthMode = 'sign-in' | 'sign-up';

export type AuthSession = {
  name: string;
  email: string;
  mode: AuthMode;
  loggedInAt: string;
};

const AUTH_SESSION_KEY = 'admin-auth-session';

function readFromStorage(storage: Storage): AuthSession | null {
  const rawValue = storage.getItem(AUTH_SESSION_KEY);

  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue) as AuthSession;
  } catch {
    storage.removeItem(AUTH_SESSION_KEY);
    return null;
  }
}

export function getAuthSession(): AuthSession | null {
  return readFromStorage(localStorage) ?? readFromStorage(sessionStorage);
}

export function isAuthenticated(): boolean {
  return Boolean(getAuthSession());
}

export function saveAuthSession(session: AuthSession): void {
  const serializedSession = JSON.stringify(session);

  // Store in both scopes so session survives refreshes and is also available per-tab.
  localStorage.setItem(AUTH_SESSION_KEY, serializedSession);
  sessionStorage.setItem(AUTH_SESSION_KEY, serializedSession);
}

export function clearAuthSession(): void {
  localStorage.removeItem(AUTH_SESSION_KEY);
  sessionStorage.removeItem(AUTH_SESSION_KEY);
}
