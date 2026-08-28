import React from 'react';
import { useAuth } from './hooks/useAuth';
import { GoogleLoginButton } from './components/auth/GoogleLoginButton';
import { AppShell } from './components/layout/AppShell';
import { Loader2 } from 'lucide-react';

export const App: React.FC = () => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-950 text-white">
        <div className="flex flex-col items-center space-y-3">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          <p className="text-xs text-slate-400 font-medium">Initializing secure enclave...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <GoogleLoginButton />;
  }

  return <AppShell />;
};

export default App;
