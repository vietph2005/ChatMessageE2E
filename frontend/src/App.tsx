import React from 'react';
import { Layers, Terminal, Sparkles, CheckCircle2, Server, Globe } from 'lucide-react';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen w-full bg-slate-950 text-slate-100 flex flex-col justify-between p-6 sm:p-10 font-sans selection:bg-blue-500/30 selection:text-blue-200">
      {/* Background glow effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-blue-600/15 rounded-full blur-3xl" />
        <div className="absolute top-1/2 -right-40 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="relative z-10 max-w-5xl mx-auto w-full flex items-center justify-between pb-8 border-b border-slate-800/80">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 shadow-lg shadow-blue-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">Starter Template</h1>
            <p className="text-xs text-slate-400">Clean architecture &amp; preserved tech stack</p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs font-medium px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>Ready to Build</span>
        </div>
      </header>

      {/* Hero Content */}
      <main className="relative z-10 max-w-5xl mx-auto w-full my-auto py-12 space-y-10">
        <div className="space-y-4 text-center sm:text-left">
          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
            Bắt đầu dự án mới <br />
            <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
              với nền tảng sẵn sàng
            </span>
          </h2>
          <p className="text-slate-400 max-w-2xl text-sm sm:text-base leading-relaxed">
            Dự án đã được dọn sạch toàn bộ mã nguồn nghiệp vụ cũ. Tech stack hoàn chỉnh bao gồm backend Spring Boot và frontend React + TypeScript + Tailwind CSS đã sẵn sàng cho bạn triển khai.
          </p>
        </div>

        {/* Stack Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Backend Card */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm space-y-4 hover:border-slate-700/80 transition-all">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                <Server className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white">Backend (Spring Boot 3)</h3>
            </div>
            <ul className="space-y-2.5 text-xs text-slate-300">
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Spring Boot 3.3.3 &amp; Java 17</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Spring Data MongoDB &amp; WebSocket (STOMP)</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Spring Security &amp; JJWT</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Lombok &amp; JUnit 5 Starter Testing</span>
              </li>
            </ul>
          </div>

          {/* Frontend Card */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm space-y-4 hover:border-slate-700/80 transition-all">
            <div className="flex items-center space-x-3">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Globe className="w-5 h-5" />
              </div>
              <h3 className="font-semibold text-white">Frontend (Vite + React)</h3>
            </div>
            <ul className="space-y-2.5 text-xs text-slate-300">
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>React 18 &amp; TypeScript 5</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Tailwind CSS &amp; PostCSS styling</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Lucide Icons &amp; STOMP Client dependencies</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Vite dev server &amp; Vitest runner</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Getting Started Guide */}
        <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800/80 space-y-3">
          <div className="flex items-center space-x-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
            <Terminal className="w-4 h-4 text-blue-400" />
            <span>Lệnh phát triển cơ bản</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/60 text-slate-300">
              <span className="text-slate-500"># Chạy backend:</span>
              <br />
              <span className="text-blue-400">mvn spring-boot:run</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/60 text-slate-300">
              <span className="text-slate-500"># Chạy frontend:</span>
              <br />
              <span className="text-indigo-400">cd frontend && npm run dev</span>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 max-w-5xl mx-auto w-full pt-6 border-t border-slate-800/80 text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-slate-400" />
          <span>Branch: starter-clean</span>
        </div>
        <span>Ready for custom development</span>
      </footer>
    </div>
  );
};

export default App;
