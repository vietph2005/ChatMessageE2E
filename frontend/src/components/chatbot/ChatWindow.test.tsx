// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ChatWindow } from './ChatWindow';
import { ChatMessageItem } from './MessageBubble';

describe('ChatWindow Component', () => {
  beforeEach(() => {
    // Mock scrollIntoView in jsdom
    window.HTMLElement.prototype.scrollIntoView = vi.fn();
  });

  it('renders welcome screen and quick prompts when messages list is empty', () => {
    render(
      <ChatWindow
        messages={[]}
        isLoading={false}
        errorMessage={null}
        onSendMessage={vi.fn()}
        onClearChat={vi.fn()}
      />
    );

    expect(screen.getByText(/Xin chào! Tôi có thể giúp gì cho bạn?/i)).toBeInTheDocument();
    expect(screen.getByText(/Tìm bạn bè/i)).toBeInTheDocument();
    expect(screen.getByText(/Bảo mật E2EE/i)).toBeInTheDocument();
  });

  it('renders message history correctly for both user and bot', () => {
    const mockMessages: ChatMessageItem[] = [
      {
        id: 'msg-1',
        role: 'user',
        content: 'Làm sao để tìm bạn bè?',
        timestamp: new Date(),
        status: 'done',
      },
      {
        id: 'msg-2',
        role: 'bot',
        content: 'Bạn hãy nhập Gmail chính xác vào ô tìm kiếm.',
        sources: [
          {
            id: 'faq-1',
            category: 'Tìm kiếm',
            question: 'Làm sao tìm người khác?',
            similarity: 0.89,
          },
        ],
        hasContext: true,
        timestamp: new Date(),
        status: 'done',
      },
    ];

    render(
      <ChatWindow
        messages={mockMessages}
        isLoading={false}
        errorMessage={null}
        onSendMessage={vi.fn()}
        onClearChat={vi.fn()}
      />
    );

    expect(screen.getByText('Làm sao để tìm bạn bè?')).toBeInTheDocument();
    expect(screen.getByText('Bạn hãy nhập Gmail chính xác vào ô tìm kiếm.')).toBeInTheDocument();
    expect(screen.getByText('Tìm kiếm')).toBeInTheDocument();
  });

  it('calls onSendMessage when clicking a quick prompt', () => {
    const mockSend = vi.fn();
    render(
      <ChatWindow
        messages={[]}
        isLoading={false}
        errorMessage={null}
        onSendMessage={mockSend}
        onClearChat={vi.fn()}
      />
    );

    const promptBtn = screen.getByText(/Tìm bạn bè/i).closest('button');
    expect(promptBtn).not.toBeNull();
    fireEvent.click(promptBtn!);

    expect(mockSend).toHaveBeenCalledWith(
      expect.stringContaining('Làm thế nào để tìm kiếm người dùng khác')
    );
  });
});
