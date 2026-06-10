// js/auth.js
const API_BASE = `/staging-api`;

export async function login(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Credenciales inválidas');
  }
  const { access_token } = await res.json();
  localStorage.setItem('token', access_token);
  // Decodifica y devuelve el payload
  return JSON.parse(atob(access_token.split('.')[1]));
}

