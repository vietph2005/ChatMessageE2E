import { describe, it, expect } from 'vitest';
import {
  generateIdentityKeyPair,
  importPeerPublicKey,
  deriveSessionKey,
  encryptText,
  decryptText,
  computeSafetyCode,
} from '../webCryptoEngine';

describe('Web Crypto Engine - E2EE Known Vectors & Mechanics', () => {
  it('should generate valid ECDH P-256 key pair and export SPKI', async () => {
    const { keyPair, publicKeyBase64 } = await generateIdentityKeyPair();
    expect(keyPair).toBeDefined();
    expect(publicKeyBase64).toBeDefined();
    expect(publicKeyBase64.length).toBeGreaterThan(50);

    const imported = await importPeerPublicKey(publicKeyBase64);
    expect(imported).toBeDefined();
    expect(imported.algorithm.name).toBe('ECDH');
  });

  it('should derive identical symmetric session key on both sides (Diffie-Hellman Property)', async () => {
    const userA = await generateIdentityKeyPair();
    const userB = await generateIdentityKeyPair();

    const peerKeyB = await importPeerPublicKey(userB.publicKeyBase64);
    const peerKeyA = await importPeerPublicKey(userA.publicKeyBase64);

    const convId = 'test_conversation_123';

    const sessionKeyA = await deriveSessionKey(userA.keyPair.privateKey, peerKeyB, convId);
    const sessionKeyB = await deriveSessionKey(userB.keyPair.privateKey, peerKeyA, convId);

    const plaintext = 'Secret E2EE message between Alice and Bob!';
    const encrypted = await encryptText(plaintext, sessionKeyA);

    expect(encrypted.ciphertext).not.toBe(plaintext);
    expect(encrypted.iv).toBeDefined();

    const decryptedByB = await decryptText(encrypted.ciphertext, encrypted.iv, sessionKeyB);
    expect(decryptedByB).toBe(plaintext);
  });

  it('should compute identical 6-digit visual Safety Code on both sides', async () => {
    const userA = await generateIdentityKeyPair();
    const userB = await generateIdentityKeyPair();
    const convId = 'conv_safety_test';

    const codeForA = await computeSafetyCode(userA.publicKeyBase64, userB.publicKeyBase64, convId);
    const codeForB = await computeSafetyCode(userB.publicKeyBase64, userA.publicKeyBase64, convId);

    expect(codeForA.safetyCode).toHaveLength(6);
    expect(codeForA.safetyCode).toBe(codeForB.safetyCode);
    expect(codeForA.fullFingerprintHex).toBe(codeForB.fullFingerprintHex);
  });
});
