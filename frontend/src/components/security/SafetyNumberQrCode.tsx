import React, { useEffect, useState } from 'react';
import QRCode from 'qrcode';

interface Props {
  conversationId: string;
  safetyCode: string;
  fullFingerprintHex: string;
}

export const SafetyNumberQrCode: React.FC<Props> = ({
  conversationId,
  safetyCode,
  fullFingerprintHex,
}) => {
  const [dataUrl, setDataUrl] = useState<string | null>(null);

  useEffect(() => {
    const payload = `e2e-safety-v1://verify?conv=${conversationId}&code=${safetyCode}&fp=${fullFingerprintHex}`;
    QRCode.toDataURL(payload, { width: 180, margin: 1 }).then(setDataUrl).catch(console.error);
  }, [conversationId, safetyCode, fullFingerprintHex]);

  if (!dataUrl) return <div className="w-44 h-44 bg-slate-900 animate-pulse rounded-2xl mx-auto" />;

  return (
    <div className="bg-white p-2.5 rounded-2xl w-fit mx-auto shadow-md">
      <img src={dataUrl} alt="Safety QR Code" className="w-40 h-40 object-contain" />
    </div>
  );
};
