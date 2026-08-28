/**
 * Web Crypto Engine - Hardware Accelerated SubtleCrypto E2EE implementation
 * Standards: ECDH (P-256), HKDF (SHA-256), AES-GCM (256-bit), SHA-256 Fingerprint
 */

export interface CryptoKeyPairExported {
  keyPair: CryptoKeyPair;
  publicKeyBase64: string;
}

export interface EncryptedPayload {
  ciphertext: string; // Base64
  iv: string; // Base64
}

export interface SafetyCodeResult {
  safetyCode: string; // 6-digit visual code
  fullFingerprintHex: string; // 64-char hex string
}

function getSubtleCrypto(): SubtleCrypto {
  if (typeof globalThis !== 'undefined' && globalThis.crypto?.subtle) {
    return globalThis.crypto.subtle;
  }
  if (typeof window !== 'undefined' && window.crypto?.subtle) {
    return window.crypto.subtle;
  }
  throw new Error('Web Crypto API (SubtleCrypto) is not supported in this environment');
}

function getRandomValues(array: Uint8Array): Uint8Array {
  if (typeof globalThis !== 'undefined' && globalThis.crypto?.getRandomValues) {
    return globalThis.crypto.getRandomValues(array);
  }
  if (typeof window !== 'undefined' && window.crypto?.getRandomValues) {
    return window.crypto.getRandomValues(array);
  }
  throw new Error('crypto.getRandomValues is not supported');
}

// Utility Helpers
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  if (typeof btoa === 'function') {
    return btoa(binary);
  }
  return Buffer.from(binary, 'binary').toString('base64');
}

export function base64ToArrayBuffer(base64: string): ArrayBuffer {
  if (typeof Buffer !== 'undefined') {
    const buf = Buffer.from(base64, 'base64');
    const ab = new ArrayBuffer(buf.length);
    const view = new Uint8Array(ab);
    for (let i = 0; i < buf.length; ++i) {
      view[i] = buf[i];
    }
    return ab;
  }
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Generates an ECDH (P-256) Identity KeyPair
 */
export async function generateIdentityKeyPair(): Promise<CryptoKeyPairExported> {
  const subtle = getSubtleCrypto();
  const keyPair = await subtle.generateKey(
    {
      name: 'ECDH',
      namedCurve: 'P-256',
    },
    true, // Extractable for IndexedDB persistence
    ['deriveKey', 'deriveBits']
  );

  const spki = await subtle.exportKey('spki', keyPair.publicKey);
  const publicKeyBase64 = arrayBufferToBase64(spki);

  return { keyPair, publicKeyBase64 };
}

/**
 * Imports a peer's public key from SPKI Base64 format
 */
export async function importPeerPublicKey(spkiBase64: string): Promise<CryptoKey> {
  const subtle = getSubtleCrypto();
  const buffer = base64ToArrayBuffer(spkiBase64);
  return await subtle.importKey(
    'spki',
    buffer,
    {
      name: 'ECDH',
      namedCurve: 'P-256',
    },
    true,
    []
  );
}

/**
 * Derives a shared symmetric AES-GCM session key using ECDH + HKDF
 */
export async function deriveSessionKey(
  myPrivateKey: CryptoKey,
  peerPublicKey: CryptoKey,
  conversationId: string
): Promise<CryptoKey> {
  const subtle = getSubtleCrypto();

  // Step 1: Compute raw shared bits with ECDH
  const sharedBits = await subtle.deriveBits(
    {
      name: 'ECDH',
      public: peerPublicKey,
    },
    myPrivateKey,
    256
  );

  // Step 2: Import shared secret for HKDF
  const hkdfKey = await subtle.importKey(
    'raw',
    sharedBits,
    { name: 'HKDF' },
    false,
    ['deriveKey']
  );

  // Step 3: Derive AES-GCM 256-bit encryption key with conversation context info
  const infoBuffer = new TextEncoder().encode(`chat-e2e-session-v1-${conversationId}`);
  const salt = new Uint8Array(32); // Zero salt

  return await subtle.deriveKey(
    {
      name: 'HKDF',
      hash: 'SHA-256',
      salt: salt,
      info: infoBuffer,
    },
    hkdfKey,
    {
      name: 'AES-GCM',
      length: 256,
    },
    false,
    ['encrypt', 'decrypt']
  );
}

/**
 * Encrypts plaintext string using AES-GCM 256-bit
 */
export async function encryptText(
  plaintext: string,
  sessionKey: CryptoKey
): Promise<EncryptedPayload> {
  const subtle = getSubtleCrypto();
  const iv = getRandomValues(new Uint8Array(12)); // 96-bit unique IV
  const encoded = new TextEncoder().encode(plaintext);

  const ciphertextBuffer = await subtle.encrypt(
    {
      name: 'AES-GCM',
      iv: iv as any,
    },
    sessionKey,
    encoded
  );

  return {
    ciphertext: arrayBufferToBase64(ciphertextBuffer),
    iv: arrayBufferToBase64(iv.buffer as ArrayBuffer),
  };
}

/**
 * Decrypts AES-GCM 256-bit ciphertext back to plaintext string
 */
export async function decryptText(
  ciphertextBase64: string,
  ivBase64: string,
  sessionKey: CryptoKey
): Promise<string> {
  const subtle = getSubtleCrypto();
  const ciphertextBuffer = base64ToArrayBuffer(ciphertextBase64);
  const ivBuffer = base64ToArrayBuffer(ivBase64);

  const decryptedBuffer = await subtle.decrypt(
    {
      name: 'AES-GCM',
      iv: new Uint8Array(ivBuffer) as any,
    },
    sessionKey,
    ciphertextBuffer
  );

  return new TextDecoder().decode(decryptedBuffer);
}

/**
 * Encrypts an image or binary file using AES-GCM
 */
export async function encryptMedia(
  fileBytes: ArrayBuffer,
  sessionKey: CryptoKey
): Promise<{ encryptedBlob: Blob; iv: string }> {
  const subtle = getSubtleCrypto();
  const iv = getRandomValues(new Uint8Array(12));

  const encryptedBuffer = await subtle.encrypt(
    {
      name: 'AES-GCM',
      iv: iv as any,
    },
    sessionKey,
    fileBytes
  );

  return {
    encryptedBlob: new Blob([encryptedBuffer], { type: 'application/octet-stream' }),
    iv: arrayBufferToBase64(iv.buffer as ArrayBuffer),
  };
}

/**
 * Decrypts encrypted media bytes to a renderable Blob
 */
export async function decryptMedia(
  encryptedBytes: ArrayBuffer,
  ivBase64: string,
  sessionKey: CryptoKey,
  mimeType: string = 'image/png'
): Promise<Blob> {
  const subtle = getSubtleCrypto();
  const ivBuffer = base64ToArrayBuffer(ivBase64);

  const decryptedBuffer = await subtle.decrypt(
    {
      name: 'AES-GCM',
      iv: new Uint8Array(ivBuffer) as any,
    },
    sessionKey,
    encryptedBytes
  );

  return new Blob([decryptedBuffer], { type: mimeType });
}

/**
 * Computes a deterministic 6-digit visual Safety Code & 64-char fingerprint (Layer 4)
 */
export async function computeSafetyCode(
  publicKeyA: string,
  publicKeyB: string,
  conversationId: string
): Promise<SafetyCodeResult> {
  const subtle = getSubtleCrypto();

  // Sort lexicographically to ensure both parties compute the exact same code
  const sortedKeys = [publicKeyA, publicKeyB].sort();
  const input = `${sortedKeys[0]}:${sortedKeys[1]}:${conversationId}`;

  const hashBuffer = await subtle.digest(
    'SHA-256',
    new TextEncoder().encode(input)
  );

  const hashBytes = new Uint8Array(hashBuffer);
  let hexString = '';
  for (let i = 0; i < hashBytes.length; i++) {
    hexString += hashBytes[i].toString(16).padStart(2, '0');
  }

  // Derive 6-digit visual decimal code from first 4 bytes
  const dataView = new DataView(hashBuffer);
  const num = Math.abs(dataView.getInt32(0, false)) % 1000000;
  const safetyCode = num.toString().padStart(6, '0');

  return {
    safetyCode,
    fullFingerprintHex: hexString,
  };
}
