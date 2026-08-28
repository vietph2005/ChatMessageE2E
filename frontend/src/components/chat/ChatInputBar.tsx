import React, { useState, useRef } from 'react';
import { Send, Image, X } from 'lucide-react';
import { stompChatService } from '../../services/stompClient';

interface Props {
  conversationId: string;
  onSendMessage: (text: string) => Promise<void>;
  onSendImage: (file: File) => Promise<void>;
  disabled?: boolean;
}

export const ChatInputBar: React.FC<Props> = ({
  conversationId,
  onSendMessage,
  onSendImage,
  disabled = false,
}) => {
  const [text, setText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setText(e.target.value);
    stompChatService.sendTyping(conversationId, e.target.value.length > 0);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert('File size exceeds 5MB limit');
        return;
      }
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const clearSelectedFile = () => {
    setSelectedFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (disabled) return;

    if (selectedFile) {
      const fileToSend = selectedFile;
      clearSelectedFile();
      await onSendImage(fileToSend);
    }

    if (text.trim()) {
      const textToSend = text.trim();
      setText('');
      stompChatService.sendTyping(conversationId, false);
      await onSendMessage(textToSend);
    }
  };

  return (
    <div className="p-3 glass-panel border-t border-white/10">
      {/* Attached file preview */}
      {previewUrl && (
        <div className="mb-2.5 p-2 bg-slate-900/90 rounded-2xl border border-white/10 flex items-center justify-between w-fit">
          <img src={previewUrl} alt="Preview" className="w-12 h-12 rounded-xl object-cover" />
          <span className="text-xs text-slate-300 ml-2 max-w-xs truncate">{selectedFile?.name}</span>
          <button
            type="button"
            onClick={clearSelectedFile}
            className="ml-2 p-1 text-slate-400 hover:text-white rounded-full hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <form onSubmit={handleSend} className="flex items-center space-x-2">
        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
          disabled={disabled}
        />

        {/* Attachment Button */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className="p-2.5 rounded-full text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors disabled:opacity-40"
          title="Attach encrypted image (max 5MB)"
        >
          <Image className="w-5 h-5" />
        </button>

        {/* Text Input */}
        <div className="flex-1 relative">
          <input
            type="text"
            value={text}
            onChange={handleTextChange}
            disabled={disabled}
            placeholder={disabled ? 'Handshake in progress...' : 'Type an encrypted message...'}
            className="w-full bg-slate-900/90 text-sm text-white placeholder:text-slate-500 px-4 py-2.5 rounded-full border border-white/10 focus:outline-none focus:border-blue-500 transition-all disabled:opacity-40"
          />
        </div>

        {/* Send Button */}
        <button
          type="submit"
          disabled={disabled || (!text.trim() && !selectedFile)}
          className="p-2.5 bg-gradient-to-tr from-messenger-gradientStart to-messenger-gradientEnd hover:opacity-90 disabled:opacity-30 text-white rounded-full shadow-md shadow-blue-500/25 transition-all transform active:scale-95 flex items-center justify-center"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
