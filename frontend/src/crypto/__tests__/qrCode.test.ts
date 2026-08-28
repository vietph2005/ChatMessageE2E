import { describe, it, expect } from 'vitest';
import QRCode from 'qrcode';

describe('QR Code Verification & Payload Generation', () => {
  it('should generate valid QR code data URL from safety payload', async () => {
    const payload = 'e2e-safety-v1://verify?conv=conv_123&code=842910&fp=abcdef';
    const dataUrl = await QRCode.toDataURL(payload, { width: 256 });

    expect(dataUrl).toBeDefined();
    expect(dataUrl.startsWith('data:image/png;base64,')).toBe(true);
  });
});
