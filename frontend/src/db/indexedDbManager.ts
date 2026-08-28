import { openDB, DBSchema, IDBPDatabase } from 'idb';

export interface LocalMessageRecord {
  id: string;
  conversationId: string;
  senderId: string;
  recipientId: string;
  messageType: 'TEXT' | 'IMAGE';
  plaintext: string;
  mediaBlob?: Blob;
  mediaObjectUrl?: string;
  sentAt: string;
  isRevoked: boolean;
  status: 'SENDING' | 'SENT' | 'DELIVERED' | 'READ';
}

export interface ConversationSessionRecord {
  conversationId: string;
  peerUserId: string;
  peerPublicKeyBase64: string;
  safetyCode: string;
  fullFingerprintHex: string;
  updatedAt: string;
}

interface ChatMessageE2EDB extends DBSchema {
  identity_keys: {
    key: string;
    value: {
      keyId: string;
      publicKeyBase64: string;
      privateKeyJwk: JsonWebKey;
      publicKeyJwk: JsonWebKey;
      createdAt: string;
    };
  };
  conversation_sessions: {
    key: string;
    value: ConversationSessionRecord;
  };
  local_messages: {
    key: string;
    value: LocalMessageRecord;
    indexes: { 'by-conversation': string };
  };
}

const DB_NAME = 'ChatMessageE2E_ClientDB';
const DB_VERSION = 1;

let dbPromise: Promise<IDBPDatabase<ChatMessageE2EDB>> | null = null;

export function getDb(): Promise<IDBPDatabase<ChatMessageE2EDB>> {
  if (!dbPromise) {
    dbPromise = openDB<ChatMessageE2EDB>(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains('identity_keys')) {
          db.createObjectStore('identity_keys', { keyPath: 'keyId' });
        }
        if (!db.objectStoreNames.contains('conversation_sessions')) {
          db.createObjectStore('conversation_sessions', { keyPath: 'conversationId' });
        }
        if (!db.objectStoreNames.contains('local_messages')) {
          const messageStore = db.createObjectStore('local_messages', { keyPath: 'id' });
          messageStore.createIndex('by-conversation', 'conversationId');
        }
      },
    });
  }
  return dbPromise;
}

export async function saveIdentityKeys(
  publicKeyBase64: string,
  keyPair: CryptoKeyPair
): Promise<void> {
  const db = await getDb();
  const privateKeyJwk = await window.crypto.subtle.exportKey('jwk', keyPair.privateKey);
  const publicKeyJwk = await window.crypto.subtle.exportKey('jwk', keyPair.publicKey);

  await db.put('identity_keys', {
    keyId: 'primary_identity',
    publicKeyBase64,
    privateKeyJwk,
    publicKeyJwk,
    createdAt: new Date().toISOString(),
  });
}

export async function loadIdentityKeyPair(): Promise<{
  keyPair: CryptoKeyPair;
  publicKeyBase64: string;
} | null> {
  const db = await getDb();
  const record = await db.get('identity_keys', 'primary_identity');
  if (!record) return null;

  const privateKey = await window.crypto.subtle.importKey(
    'jwk',
    record.privateKeyJwk,
    { name: 'ECDH', namedCurve: 'P-256' },
    true,
    ['deriveKey', 'deriveBits']
  );

  const publicKey = await window.crypto.subtle.importKey(
    'jwk',
    record.publicKeyJwk,
    { name: 'ECDH', namedCurve: 'P-256' },
    true,
    []
  );

  return {
    keyPair: { privateKey, publicKey },
    publicKeyBase64: record.publicKeyBase64,
  };
}

export async function saveSessionRecord(record: ConversationSessionRecord): Promise<void> {
  const db = await getDb();
  await db.put('conversation_sessions', record);
}

export async function getSessionRecord(conversationId: string): Promise<ConversationSessionRecord | undefined> {
  const db = await getDb();
  return await db.get('conversation_sessions', conversationId);
}

export async function saveLocalMessage(msg: LocalMessageRecord): Promise<void> {
  const db = await getDb();
  await db.put('local_messages', msg);
}

export async function getMessagesByConversation(conversationId: string): Promise<LocalMessageRecord[]> {
  const db = await getDb();
  return await db.getAllFromIndex('local_messages', 'by-conversation', conversationId);
}

export async function revokeLocalMessage(messageId: string): Promise<void> {
  const db = await getDb();
  const msg = await db.get('local_messages', messageId);
  if (msg) {
    msg.isRevoked = true;
    msg.plaintext = 'This message was unsent';
    await db.put('local_messages', msg);
  }
}
