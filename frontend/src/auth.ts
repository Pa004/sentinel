/* GitHub OAuth authentication for the frontend. */

const API_URL = import.meta.env.VITE_API_URL || "";

export function login() {
  window.location.href = `${API_URL}/auth/github`;
}

export function getToken(): string | null {
  return localStorage.getItem("sentinel_token");
}

export function setToken(token: string) {
  localStorage.setItem("sentinel_token", token);
}

export function removeToken() {
  localStorage.removeItem("sentinel_token");
}

export function logout() {
  removeToken();
  window.location.reload();
}

export function isAuthenticated(): boolean {
  const token = getToken();
  if (!token) return false;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload.exp * 1000 > Date.now();
  } catch {
    return false;
  }
}

export function getUser(): { username: string; github_id: number } | null {
  const token = getToken();
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return { username: payload.username, github_id: parseInt(payload.sub) };
  } catch {
    return null;
  }
}

export function handleCallback(): boolean {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");
  if (token) {
    setToken(token);
    window.history.replaceState({}, "", "/");
    return true;
  }
  return false;
}
