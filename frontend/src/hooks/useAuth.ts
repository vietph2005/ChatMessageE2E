import { useState, useEffect, createContext, useContext, ReactNode, createElement } from 'react';
import { apiClient, UserProfileDto } from '../services/apiClient';
import { generateIdentityKeyPair } from '../crypto/webCryptoEngine';
import { loadIdentityKeyPair, saveIdentityKeys } from '../db/indexedDbManager';

interface AuthContextType {
  user: UserProfileDto | null;
  token: string | null;
  publicKeyBase64: string | null;
  isLoading: boolean;
  loginWithGoogleToken: (idToken: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfileDto | null>(() => {
    const saved = localStorage.getItem('auth_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(null);
  const [publicKeyBase64, setPublicKeyBase64] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize or load local cryptographic identity keys and restore session
  useEffect(() => {
    async function initAuthAndKeys() {
      try {
        // 1. Try to restore session from HttpOnly Cookie
        let currentUser: UserProfileDto | null = null;
        try {
          currentUser = await apiClient.getCurrentUser();
          setUser(currentUser);
          localStorage.setItem('auth_user', JSON.stringify(currentUser));
        } catch {
          // Cookie expired or not logged in
          setUser(null);
          localStorage.removeItem('auth_user');
        }

        // 2. Load or generate local cryptographic identity keys
        let keys = await loadIdentityKeyPair();
        if (!keys) {
          const generated = await generateIdentityKeyPair();
          await saveIdentityKeys(generated.publicKeyBase64, generated.keyPair);
          keys = generated;
        }
        setPublicKeyBase64(keys.publicKeyBase64);

        // 3. If authenticated, ensure public keys are registered on backend
        if (currentUser && keys.publicKeyBase64) {
          await apiClient.registerPublicKeyBundle({
            userId: currentUser.id,
            identityPublicKey: keys.publicKeyBase64,
            signedPreKey: keys.publicKeyBase64, // active pre-key
            preKeySignature: 'auto-signed',
          }).catch(console.warn);
        }
      } catch (e) {
        console.error('Failed to init auth/crypto keys', e);
      } finally {
        setIsLoading(false);
      }
    }

    initAuthAndKeys();
  }, []);

  const loginWithGoogleToken = async (idToken: string) => {
    setIsLoading(true);
    try {
      const res = await apiClient.authenticateWithGoogle(idToken);
      apiClient.setToken(res.accessToken);
      setToken(res.accessToken);
      setUser(res.user);
      localStorage.setItem('auth_user', JSON.stringify(res.user));

      // Register public keys on backend
      let keys = await loadIdentityKeyPair();
      if (!keys) {
        const generated = await generateIdentityKeyPair();
        await saveIdentityKeys(generated.publicKeyBase64, generated.keyPair);
        keys = generated;
      }
      setPublicKeyBase64(keys.publicKeyBase64);

      await apiClient.registerPublicKeyBundle({
        userId: res.user.id,
        identityPublicKey: keys.publicKeyBase64,
        signedPreKey: keys.publicKeyBase64,
        preKeySignature: 'auto-signed',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await apiClient.logout();
    } catch (e) {
      console.warn('Logout request error', e);
    }
    apiClient.setToken(null);
    setToken(null);
    setUser(null);
    localStorage.removeItem('auth_user');
  };

  return createElement(
    AuthContext.Provider,
    { value: { user, token, publicKeyBase64, isLoading, loginWithGoogleToken, logout } },
    children
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

