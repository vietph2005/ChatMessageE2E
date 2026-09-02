import React from 'react';
import { BookOpen } from 'lucide-react';
import { FaqSource } from '../../services/chatbotService';

interface SourceBadgeProps {
  source: FaqSource;
}

export const SourceBadge: React.FC<SourceBadgeProps> = ({ source }) => {
  const percent = Math.round(source.similarity * 100);

  return (
    <div
      className="group relative inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-900/30 text-blue-300 border border-blue-700/40 hover:bg-blue-800/40 transition-colors cursor-help"
      title={`FAQ gốc: "${source.question}"`}
    >
      <BookOpen className="w-3 h-3 text-blue-400" />
      <span>{source.category}</span>
      <span className="text-[10px] text-blue-400/80 bg-blue-950/60 px-1.5 py-0.5 rounded-full font-mono">
        {percent}%
      </span>

      {/* Tooltip on hover */}
      <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block z-50 w-64 p-2 bg-slate-900 text-slate-200 text-xs rounded-lg shadow-xl border border-slate-700 pointer-events-none">
        <p className="font-semibold text-blue-400 mb-0.5">Câu hỏi FAQ liên quan:</p>
        <p className="line-clamp-2">{source.question}</p>
      </div>
    </div>
  );
};
