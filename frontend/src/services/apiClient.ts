export interface UserProfileDto {
  id: string;
  email: string;
  displayName: string;
  avatarUrl: string;
  isOnline: boolean;
}

export interface PublicKeyBundleDto {
  userId: string;
  identityPublicKey: string;
  signedPreKey: string;
  preKeySignature: string;
  keyVersion?: number;
}

export interface ConversationSummaryDto {
  id: string;
  peerUser: UserProfileDto;
  status: 'INITIATING' | 'PENDING_ACCEPTANCE' | 'HANDSHAKE_IN_PROGRESS' | 'VERIFIED_ACTIVE' | 'BLOCKED';
  lastMessageSnippet?: string;
  lastMessageAt?: string;
  unreadCount: number;
}

export interface ConversationDetailDto {
  id: string;
  participantAId: string;
  participantBId: string;
  status: string;
  handshake: {
    initiatorPublicKey?: string;
    recipientPublicKey?: string;
    layer1Status: string;
    layer2Status: string;
    layer3Status: string;
    layer4Status: string;
    safetyCode: string;
    fullFingerprintHex: string;
    version?: number;
  };
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(endpoint, {
      ...options,
      credentials: 'include',
      headers,
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { message: response.statusText };
      }
      throw new Error(errorData.message || `HTTP ${response.status}: Request failed`);
    }

    // Return null or empty object if 204 or no content
    const text = await response.text();
    return text ? JSON.parse(text) : ({} as T);
  }

  // Auth APIs
  async authenticateWithGoogle(idToken: string): Promise<{ accessToken: string; expiresIn: number; user: UserProfileDto }> {
    return await this.request('/api/v1/auth/google', {
      method: 'POST',
      body: JSON.stringify({ idToken }),
    });
  }

  async getCurrentUser(): Promise<UserProfileDto> {
    return await this.request('/api/v1/auth/me');
  }

  async logout(): Promise<void> {
    await this.request('/api/v1/auth/logout', {
      method: 'POST',
    });
    this.token = null;
  }

  // User APIs
  async searchUserByGmail(email: string): Promise<UserProfileDto> {
    return await this.request(`/api/v1/users/search?email=${encodeURIComponent(email)}`);
  }

  async registerPublicKeyBundle(bundle: PublicKeyBundleDto): Promise<void> {
    await this.request('/api/v1/users/keys', {
      method: 'POST',
      body: JSON.stringify(bundle),
    });
  }

  async getPeerPublicKeyBundle(userId: string): Promise<PublicKeyBundleDto> {
    return await this.request(`/api/v1/users/keys?userId=${encodeURIComponent(userId)}`);
  }

  // Conversation & 4-Layer Handshake APIs
  async listConversations(): Promise<ConversationSummaryDto[]> {
    return await this.request('/api/v1/conversations');
  }

  async getConversationDetail(conversationId: string): Promise<ConversationDetailDto> {
    return await this.request(`/api/v1/conversations/${conversationId}`);
  }

  async initiateConversation(recipientEmail: string, initiatorPublicKey: string): Promise<ConversationDetailDto> {
    return await this.request('/api/v1/conversations', {
      method: 'POST',
      body: JSON.stringify({ recipientEmail, initiatorPublicKey }),
    });
  }

  async acceptHandshake(conversationId: string, recipientPublicKey: string): Promise<ConversationDetailDto> {
    return await this.request(`/api/v1/conversations/${conversationId}/handshake/accept`, {
      method: 'POST',
      body: JSON.stringify({ recipientPublicKey }),
    });
  }

  async confirmSafetyCode(conversationId: string, safetyCode: string): Promise<ConversationDetailDto> {
    return await this.request(`/api/v1/conversations/${conversationId}/handshake/confirm-safety-code`, {
      method: 'POST',
      body: JSON.stringify({ safetyCode }),
    });
  }

  async reInitiateHandshake(conversationId: string, initiatorPublicKey: string): Promise<ConversationDetailDto> {
    return await this.request(`/api/v1/conversations/${conversationId}/handshake/re-initiate`, {
      method: 'POST',
      body: JSON.stringify({ initiatorPublicKey }),
    });
  }

  async uploadEncryptedMedia(conversationId: string, encryptedBlob: Blob): Promise<{ mediaUrl: string; mediaId: string }> {
    const formData = new FormData();
    formData.append('encryptedFile', encryptedBlob, 'encrypted.bin');
    formData.append('conversationId', conversationId);

    const headers: Record<string, string> = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch('/api/v1/media/upload', {
      method: 'POST',
      credentials: 'include',
      headers,
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Media upload failed with status ${response.status}`);
    }

    return await response.json();
  }

  async blockUser(userId: string): Promise<void> {
    await this.request(`/api/v1/users/block`, {
      method: 'POST',
      body: JSON.stringify({ userId }),
    });
  }

  async unblockUser(userId: string): Promise<void> {
    await this.request(`/api/v1/users/unblock`, {
      method: 'POST',
      body: JSON.stringify({ userId }),
    });
  }
}

export const apiClient = new ApiClient();

