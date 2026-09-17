import * as CryptoJS from 'crypto-js';

const STORAGE_KEY = import.meta.env.VITE_STORAGE_KEY || 'default_secure_key_12345';
const TOKEN_KEY = 'enc_access_token';

export const TokenService = {
  setToken: (token: string) => {
    if (!token) return;
    try {
      const encrypted = CryptoJS.AES.encrypt(token, STORAGE_KEY).toString();
      localStorage.setItem(TOKEN_KEY, encrypted);
    } catch (e) {
      console.error('Error encrypting token', e);
    }
  },

  getToken: (): string | null => {
    const encrypted = localStorage.getItem(TOKEN_KEY);
    // Legacy support for plain text 'access_token'
    const legacy = localStorage.getItem('access_token');
    if (legacy) {
      TokenService.setToken(legacy);
      localStorage.removeItem('access_token');
      return legacy;
    }
    
    if (!encrypted) return null;
    
    try {
      const bytes = CryptoJS.AES.decrypt(encrypted, STORAGE_KEY);
      const decrypted = bytes.toString(CryptoJS.enc.Utf8);
      return decrypted || null;
    } catch (e) {
      console.error('Error decrypting token', e);
      return null;
    }
  },

  removeToken: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem('access_token'); // Clean up legacy
  }
};
