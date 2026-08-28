import React, { useEffect, useState } from 'react';
import QRCode from 'qrcode';
import { ShieldCheck, Copy, Check, X, QrCode as QrIcon } from 'lucide-react';

interface Props {
  conversationId: string;
  safetyCode: string;
  fullFingerprintHex: string;
  peerName: string;
  onClose: () => void;
}

export const SafetyQrCodeModal: React.FC<Props> = ({
  conversationId,
  safetyCode,
  fullFingerprintHex,
  peerName,
  onClose,
}) => {
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const payload = `e2e-safety-v1://verify?conv=${conversationId}&code=${safetyCode}&fp=${fullFingerprintHex}`;
    QRCode.toDataURL(payload, {
      width: 200,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#ffffff',
      },
    }).then(setQrDataUrl).catch(console.error);
  }, [conversationId, safetyCode, fullFingerprintHex]);

  const handleCopy = () => {
    navigator.clipboard.writeText(safetyCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-sm p-6 glass-panel rounded-3xl border border-white/10 text-center shadow-2xl animate-in zoom-in-95">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2 text-white font-bold text-sm">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
            <span>Safety Number & QR Code</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-slate-400 hover:text-white hover:bg-slate-800"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <p className="text-xs text-slate-400 mb-4">
          Scan this QR code or compare the 6-digit number on <span className="text-slate-200 font-semibold">{peerName}</span>'s device to verify E2EE authenticity.
        </p>

        {/* QR Code */}
        <div className="w-48 h-48 mx-auto bg-white p-2.5 rounded-2xl shadow-lg shadow-cyan-500/10 flex items-center justify-center mb-4">
          {qrDataUrl ? (
            <img src={qrDataUrl} alt="Safety QR Code" className="w-full h-full object-contain" />
          ) : (
            <QrIcon className="w-12 h-12 text-slate-400 animate-pulse" />
          )}
        </div>

        {/* 6-Digit Number */}
        <div className="p-3 bg-slate-900 rounded-2xl border border-cyan-500/30 flex items-center justify-between mb-3">
          <div className="text-xl font-mono font-bold tracking-widest text-cyan-300">
            {safetyCode.slice(0, 3)} {safetyCode.slice(3)}
          </div>
          <button
            onClick={handleCopy}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs flex items-center space-x-1"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>

        {/* Fingerprint snippet */}
        <p className="text-[10px] font-mono text-slate-500 truncate" title={fullFingerprintHex}>
          FP: {fullFingerprintHex}
        </p>
      </div>
    </div>
  );
};
