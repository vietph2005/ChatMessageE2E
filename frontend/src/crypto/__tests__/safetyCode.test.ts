import { describe, it, expect } from 'vitest';
import { computeSafetyCode } from '../webCryptoEngine';

describe('Safety Code 6-Digit Verification', () => {
  it('should generate a 6-digit decimal formatted string', async () => {
    const keyA = 'MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEKeyA1234567890';
    const keyB = 'MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEKeyB0987654321';
    const convId = 'conv_uuid_test';

    const res = await computeSafetyCode(keyA, keyB, convId);

    expect(res.safetyCode).toMatch(/^\d{6}$/);
    expect(res.fullFingerprintHex).toHaveLength(64);
  });

  it('should be symmetric regardless of who initiates', async () => {
    const keyA = 'KeyAAA';
    const keyB = 'KeyBBB';
    const convId = 'conv_1';

    const res1 = await computeSafetyCode(keyA, keyB, convId);
    const res2 = await computeSafetyCode(keyB, keyA, convId);

    expect(res1.safetyCode).toBe(res2.safetyCode);
    expect(res1.fullFingerprintHex).toBe(res2.fullFingerprintHex);
  });
});
