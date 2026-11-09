import { TokenService } from './TokenService';
import { cerrarSesion } from './session';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const HOST_API_URL = import.meta.env.VITE_HOST_API_URL || 'https://host.example.com';
export const WS_URL = API_URL.replace(/^http/, 'ws');

export const apiFetch = async <T = any>(endpoint: string, options: RequestInit = {}): Promise<T> => {
  const token = TokenService.getToken();
  
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (response.status === 401) {
      cerrarSesion();
      window.location.href = '/login';
    }
    throw new Error(data.detail || data.message || 'Error en la petición');
  }

  return data;
};
