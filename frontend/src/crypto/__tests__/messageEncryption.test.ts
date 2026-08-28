import { describe, it, expect } from 'vitest';
import {
  generateIdentityKeyPair,
  importPeerPublicKey,
  deriveSessionKey,
  encryptMedia,
  decryptMedia,
} from '../webCryptoEngine';

describe('Message & Media Encryption Engine Tests', () => {
  it('should encrypt and decrypt media file bytes cleanly', async () => {
    const userA = await generateIdentityKeyPair();
    const userB = await generateIdentityKeyPair();

    const peerKeyB = await importPeerPublicKey(userB.publicKeyBase64);
    const peerKeyA = await importPeerPublicKey(userA.publicKeyBase64);

    const sessionKeyA = await deriveSessionKey(userA.keyPair.privateKey, peerKeyB, 'conv_media');
    const sessionKeyB = await deriveSessionKey(userB.keyPair.privateKey, peerKeyA, 'conv_media');

    // Create sample fake image bytes
    const sampleBytes = new Uint8Array([137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13]);
    const { encryptedBlob, iv } = await encryptMedia(sampleBytes.buffer, sessionKeyA);

    expect(encryptedBlob).toBeDefined();
    expect(encryptedBlob.size).toBeGreaterThan(0);

    const encryptedArrayBuffer = await encryptedBlob.arrayBuffer();
    const decryptedBlob = await decryptMedia(encryptedArrayBuffer, iv, sessionKeyB, 'image/png');

    const decryptedArrayBuffer = await decryptedBlob.arrayBuffer();
    const decryptedBytes = new Uint8Array(decryptedArrayBuffer);

    expect(decryptedBytes).toEqual(sampleBytes);
  });
});
