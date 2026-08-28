import React, { useState } from 'react';
import { GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { useAuth } from '../../hooks/useAuth';
import { Shield, UserCheck, Lock } from 'lucide-react';

export const GoogleLoginButton: React.FC = () => {
  const { loginWithGoogleToken } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const handleGoogleSuccess = async (response: CredentialResponse) => {
    if (response.credential) {
      setError(null);
      try {
        await loginWithGoogleToken(response.credential);
      } catch (e: any) {
        setError(e.message || 'Xác thực Google thất bại');
      }
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 px-4 py-8 relative">
      {/* Ambient Glow Effects */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 left-1/3 w-80 h-80 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 w-full max-w-md p-8 glass-panel rounded-3xl shadow-2xl border border-white/10 flex flex-col items-center text-center">
        {/* App Logo & Badge */}
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-messenger-gradientStart to-messenger-gradientEnd flex items-center justify-center shadow-lg shadow-blue-500/30 mb-6">
          <Shield className="w-9 h-9 text-white" />
        </div>

        <h1 className="text-3xl font-extrabold text-white tracking-tight">ChatMessage E2E</h1>
        <p className="text-slate-400 text-sm mt-2 font-medium max-w-xs">
          Hệ thống Chat Bảo mật 1-1 Mã hóa Đầu Cuối & Xác thực 4 Lớp
        </p>

        {/* Security Highlights */}
        <div className="my-6 w-full grid grid-cols-2 gap-2 text-left">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-white/5 flex items-center space-x-2.5">
            <Lock className="w-4 h-4 text-cyan-400 shrink-0" />
            <span className="text-xs text-slate-300 font-semibold">Zero-Knowledge</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-900/60 border border-white/5 flex items-center space-x-2.5">
            <UserCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="text-xs text-slate-300 font-semibold">Xác thực 4 Lớp</span>
          </div>
        </div>

        {error && (
          <div className="w-full mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs text-left">
            {error}
          </div>
        )}

        {/* Official Google OAuth2 Button */}
        <div className="w-full my-4 flex flex-col items-center">
          <div className="w-full flex justify-center py-2">
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={() => setError('Đăng nhập Google thất bại hoặc cửa sổ đăng nhập đã bị đóng.')}
              theme="filled_blue"
              shape="pill"
              size="large"
              width="320"
              text="continue_with"
            />
          </div>
        </div>

        <p className="text-[11px] text-slate-500 mt-6 leading-relaxed">
          Khóa mật mã riêng tư được sinh và lưu trữ cục bộ trong IndexedDB của trình duyệt, không bao giờ gửi lên máy chủ.
        </p>
      </div>
    </div>
  );
};
