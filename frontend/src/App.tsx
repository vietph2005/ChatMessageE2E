import React, { useState, useEffect } from 'react';
import { useAuth } from './hooks/useAuth';
import { GoogleLoginButton } from './components/auth/GoogleLoginButton';
import { AppShell } from './components/layout/AppShell';
import { ChatbotPage } from './pages/ChatbotPage';
import { Loader2, Bot } from 'lucide-react';

export const App: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [showChatbot, setShowChatbot] = useState<boolean>(() => {
    return window.location.pathname.toLowerCase() === '/chatbot';
  });

  // Listen to browser history changes (e.g. Back/Forward)
  useEffect(() => {
    const handlePopState = () => {
      setShowChatbot(window.location.pathname.toLowerCase() === '/chatbot');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const openChatbot = () => {
    window.history.pushState({}, '', '/chatbot');
    setShowChatbot(true);
  };

  const closeChatbot = () => {
    window.history.pushState({}, '', '/');
    setShowChatbot(false);
  };

  if (showChatbot) {
    return <ChatbotPage onBack={closeChatbot} />;
  }

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
    return (
      <div className="relative h-screen w-screen">
        <GoogleLoginButton />
        {/* Floating FAQ button for guest users */}
        <button
          type="button"
          onClick={openChatbot}
          className="fixed bottom-6 right-6 flex items-center gap-2 px-4 py-2.5 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-xl shadow-blue-500/20 hover:scale-105 active:scale-95 transition-all z-50 border border-white/20"
        >
          <Bot className="w-4 h-4" />
          <span>Hỏi Trợ lý AI (FAQ)</span>
        </button>
      </div>
    );
  }

  return (
    <div className="relative h-screen w-screen">
      <AppShell />
      {/* Floating FAQ button inside app */}
      <button
        type="button"
        onClick={openChatbot}
        className="fixed bottom-5 right-5 flex items-center gap-2 px-3.5 py-2.5 rounded-full bg-slate-900/90 hover:bg-blue-600 text-slate-200 hover:text-white text-xs font-medium shadow-2xl border border-slate-700/60 hover:border-blue-400 transition-all hover:scale-105 active:scale-95 z-40 backdrop-blur-md"
        title="Mở Trợ lý Hỗ trợ AI (RAG FAQ)"
      >
        <Bot className="w-4 h-4 text-blue-400 group-hover:text-white" />
        <span className="hidden md:inline">Trợ lý AI</span>
      </button>
    </div>
  );
};

export default App;

