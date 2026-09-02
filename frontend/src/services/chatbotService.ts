export interface FaqSource {
  id: string;
  category: string;
  question: string;
  similarity: number;
}

export interface ChatbotResponse {
  answer: string;
  sources: FaqSource[];
  hasContext: boolean;
}

export class ChatbotService {
  private static BASE_URL = '/api/chatbot';

  static async ask(question: string): Promise<ChatbotResponse> {
    const response = await fetch(`${this.BASE_URL}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { message: response.statusText };
      }
      throw new Error(errorData.message || `Lỗi máy chủ (HTTP ${response.status})`);
    }

    return await response.json();
  }
}
