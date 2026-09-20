import { useState, useEffect, useRef } from 'react';
import { ChatUserSession } from '../types';
import { StompChatClient } from '../services/stompClient';

export interface Message {
  id: string;
  senderId: string;
  senderName: string;
  content: string;
  timestamp: string;
  isMe: boolean;
}

export interface ChatConversation {
  id: string;
  name: string;
  avatar?: string;
  lastMessage: string;
  time: string;
  unreadCount?: number;
  isOnline: boolean;
}

export const useChat = () => {
  // 1. Lấy thông tin user đăng nhập và phòng thực tế từ sessionStorage
  const storedUser: ChatUserSession | null = (() => {
    try {
      const data = sessionStorage.getItem('chat_user');
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  })();

  const currentUserName = storedUser?.userName || 'Bạn';
  const currentRoomId = storedUser?.roomId || '';

  // 2. Khởi tạo danh sách tin nhắn từ dữ liệu phòng thực tế (hoặc mảng rỗng nếu chưa có)
  const [messages, setMessages] = useState<Message[]>(() => {
    const rawMessages = storedUser?.room?.messages;
    if (Array.isArray(rawMessages) && rawMessages.length > 0) {
      return rawMessages.map((m: any, index: number) => ({
        id: m.id || `msg-${index}-${Date.now()}`,
        senderId: m.sender || m.senderId || 'unknown',
        senderName: m.sender || m.senderName || 'Người dùng',
        content: m.content || '',
        timestamp: m.timeStamp
          ? new Date(m.timeStamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isMe: (m.sender || m.senderId) === currentUserName,
      }));
    }
    return [];
  });

  const [inputText, setInputText] = useState('');

  // 3. Quản lý instance STOMP Client bằng useRef
  const stompClientRef = useRef<StompChatClient | null>(null);

  // 4. Kết nối STOMP khi có currentRoomId và dọn dẹp khi unmount / đổi phòng
  useEffect(() => {
    if (!currentRoomId) {
      console.warn('[useChat ⚠️] Không tìm thấy roomId, bỏ qua kết nối STOMP');
      return;
    }

    console.log('[useChat 🔌 KHỞI TẠO STOMP] Đang chuẩn bị kết nối vào phòng:', currentRoomId);
    const client = new StompChatClient();
    stompClientRef.current = client;

    // Kích hoạt kết nối và đăng ký nhận tin nhắn mới từ topic
    client.connect(
      currentRoomId,
      (incomingMsg: any) => {
        console.log('[useChat 📩 TIN NHẮN REALTIME ĐẾN]', incomingMsg);

        const senderName = incomingMsg.sender || incomingMsg.senderName || 'Người dùng';
        const isMe = senderName === currentUserName;

        const newMsg: Message = {
          id: incomingMsg.id || `msg-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
          senderId: incomingMsg.senderId || senderName,
          senderName: senderName,
          content: incomingMsg.content || '',
          timestamp: incomingMsg.timeStamp
            ? new Date(incomingMsg.timeStamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isMe: isMe,
        };

        // Thêm tin nhắn mới vào danh sách hiển thị
        setMessages((prev) => [...prev, newMsg]);
      },
      (status) => {
        console.log('[useChat 📶 TRẠNG THÁI STOMP]', status);
      }
    );

    // Cleanup: Ngắt kết nối STOMP an toàn khi rời trang hoặc đổi phòng
    return () => {
      console.log('[useChat 🛑 CLEANUP] Rời phòng chat, tiến hành đóng STOMP...');
      client.disconnect();
      stompClientRef.current = null;
    };
  }, [currentRoomId, currentUserName]);

  // 5. States quản lý giao diện Sidebar và tìm kiếm
  const [showRightSidebar, setShowRightSidebar] = useState(true);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);
  const [activeTab, setActiveTab] = useState<'all' | 'unread'>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // 6. Danh sách hội thoại thực tế của người dùng hiện tại
  const [conversations] = useState<ChatConversation[]>(() => {
    if (currentRoomId) {
      return [
        {
          id: currentRoomId,
          name: `Phòng ${currentRoomId}`,
          lastMessage: messages.length > 0 ? messages[messages.length - 1].content : 'Chưa có tin nhắn mới',
          time: 'Vừa xong',
          isOnline: true,
        },
      ];
    }
    return [];
  });

  // 7. Tự động cuộn xuống cuối khung chat
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 8. Xử lý gửi tin nhắn qua STOMP WebSocket
  const handleSendMessage = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim()) return;

    const trimmedContent = inputText.trim();

    if (!stompClientRef.current) {
      console.error('[useChat ❌] STOMP Client chưa được khởi tạo!');
      return;
    }

    console.log('[useChat 📤 GỬI TIN QUA STOMP]', {
      content: trimmedContent,
      sender: currentUserName,
      roomId: currentRoomId,
    });

    // Gửi tin nhắn lên Spring Boot Broker qua STOMP
    const success = stompClientRef.current.sendMessage({
      content: trimmedContent,
      sender: currentUserName,
      roomId: currentRoomId,
    });

    if (success) {
      setInputText('');
    } else {
      console.warn('[useChat ⚠️ Gửi không thành công do kết nối]');
    }
  };

  return {
    currentUserName,
    currentRoomId,
    messages,
    inputText,
    setInputText,
    conversations,
    showRightSidebar,
    setShowRightSidebar,
    showMobileSidebar,
    setShowMobileSidebar,
    activeTab,
    setActiveTab,
    searchTerm,
    setSearchTerm,
    messagesEndRef,
    handleSendMessage,
  };
};
