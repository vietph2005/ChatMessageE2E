import { Client, IMessage, StompSubscription } from '@stomp/stompjs';
import SockJS from 'sockjs-client';
import { baseURL } from '../config/App.config';
import { StompStatus } from '../types';

/**
 * Payload gửi tin nhắn STOMP tới Backend
 * Tương ứng với ChatMessageRequest DTO ở Spring Boot
 */
export interface StompMessagePayload {
  content: string;
  sender: string;
  roomId: string;
  localDateTime?: string;
}

export type MessageCallback = (message: any) => void;
export type StatusCallback = (status: StompStatus) => void;

/**
 * Quản lý kết nối STOMP qua SockJS cho ứng dụng Chat
 */
export class StompChatClient {
  private client: Client | null = null;
  private subscription: StompSubscription | null = null;

  /**
   * Khởi tạo kết nối STOMP qua SockJS và lắng nghe tin nhắn của phòng
   * @param roomId Mã phòng chat cần tham gia
   * @param onMessageCallback Callback nhận tin nhắn mới từ WebSocket
   * @param onStatusCallback Callback cập nhật trạng thái kết nối
   */
  public connect(
    roomId: string,
    onMessageCallback?: MessageCallback,
    onStatusCallback?: StatusCallback
  ): void {
    const socketUrl = `${baseURL}/chat`;
    console.log('=====================================================');
    console.log('[STOMP 1] Chuẩn bị kết nối tới Backend URL:', socketUrl);
    console.log('[STOMP 1] Phòng chat mục tiêu:', roomId);

    if (onStatusCallback) {
      onStatusCallback('CONNECTING');
    }

    // Khởi tạo STOMP Client
    this.client = new Client({
      // 1. Tạo SockJS kết nối tới endpoint /chat
      webSocketFactory: () => {
        console.log('[STOMP 2] Khởi tạo đối tượng SockJS:', socketUrl);
        return new SockJS(socketUrl);
      },

      // Tự động kết nối lại sau 5 giây nếu mất mạng
      reconnectDelay: 5000,
      heartbeatIncoming: 4000,
      heartbeatOutgoing: 4000,

      // In log chi tiết của giao thức STOMP
      debug: (msg: string) => {
        console.log('[STOMP 3 - DEBUG GIAO THỨC]', msg);
      },

      // 2. Khi bắt tay STOMP thành công
      onConnect: (frame) => {
        console.log('[STOMP 4 ✅ THÀNH CÔNG] Đã kết nối STOMP tới Backend!');
        console.log('[STOMP 4 ✅ THÀNH CÔNG] Frame chi tiết:', frame);

        if (onStatusCallback) {
          onStatusCallback('CONNECTED');
        }

        // 3. Tự động đăng ký (Subscribe) topic của phòng: /topic/room/{roomId}
        const topic = `/topic/room/${roomId}`;
        console.log('[STOMP 5 📡 SUBSCRIBE] Đang đăng ký lắng nghe kênh:', topic);

        if (this.subscription) {
          this.subscription.unsubscribe();
        }

        this.subscription = this.client!.subscribe(topic, (message: IMessage) => {
          console.log('[STOMP 6 📩 TIN NHẮN MỚI] Nhận được tin nhắn từ:', topic);
          console.log('[STOMP 6 📩 TIN NHẮN MỚI] Raw body:', message.body);

          try {
            const parsedMessage = JSON.parse(message.body);
            console.log('[STOMP 6 📩 TIN NHẮN MỚI] Dữ liệu JSON sau khi parse:', parsedMessage);
            if (onMessageCallback) {
              onMessageCallback(parsedMessage);
            }
          } catch (err) {
            console.error('[STOMP 6 ❌ LỖI PARSE JSON]', err, message.body);
          }
        });
      },

      // Khi có lỗi từ STOMP Broker
      onStompError: (frame) => {
        console.error('[STOMP ❌ LỖI BROKER]', frame.headers['message'], frame.body);
        if (onStatusCallback) {
          onStatusCallback('ERROR');
        }
      },

      // Khi WebSocket đóng
      onWebSocketClose: (event) => {
        console.warn('[STOMP ⚠️ ĐÃ ĐÓNG KẾT NỐI]', event);
        if (onStatusCallback) {
          onStatusCallback('DISCONNECTED');
        }
      },

      // Khi WebSocket bị lỗi
      onWebSocketError: (error) => {
        console.error('[STOMP ❌ LỖI WEBSOCKET]', error);
        if (onStatusCallback) {
          onStatusCallback('ERROR');
        }
      },
    });

    // 4. Kích hoạt kết nối STOMP
    console.log('[STOMP 🚀 BẮT ĐẦU] Gọi client.activate()...');
    this.client.activate();
  }

  /**
   * =========================================================================
   * GỬI TIN NHẮN (PUBLISH) QUA GIAO THỨC STOMP
   * =========================================================================
   * @param payload Dữ liệu tin nhắn gồm content, sender, roomId, localDateTime
   * @returns boolean true nếu đã gửi thành công lên broker
   */
  public sendMessage(payload: StompMessagePayload): boolean {
    console.log('---------------------------------------------------------');
    console.log('[STOMP 📤 GỬI TIN NHẮN] Chuẩn bị gửi tin nhắn...');

    // 1. Kiểm tra trạng thái kết nối
    if (!this.client || !this.client.connected) {
      console.warn('[STOMP ⚠️ GỬI THẤT BẠI] Client chưa kết nối hoặc đang mất kết nối tới Backend!');
      return false;
    }

    // 2. Xác định đích đến (Destination) - khớp với @MessageMapping("sendMessage/{roomId}")
    const destination = `/app/sendMessage/${payload.roomId}`;
    console.log('[STOMP 📤 GỬI TIN NHẮN] Đích gửi (Destination):', destination);
    console.log('[STOMP 📤 GỬI TIN NHẮN] Dữ liệu gửi (Payload):', payload);

    try {
      // 3. Thực hiện gửi frame STOMP SEND
      this.client.publish({
        destination: destination,
        body: JSON.stringify(payload),
      });

      console.log('[STOMP ✅ GỬI THÀNH CÔNG] Đã publish tin nhắn lên broker thành công!');
      return true;
    } catch (error) {
      console.error('[STOMP ❌ LỖI KHI GỬI]', error);
      return false;
    }
  }

  /**
   * Ngắt kết nối STOMP an toàn
   */
  public disconnect(): void {
    console.log('[STOMP 🛑 NGẮT KẾT NỐI] Đang hủy đăng ký và đóng client...');
    if (this.subscription) {
      this.subscription.unsubscribe();
      this.subscription = null;
    }
    if (this.client) {
      this.client.deactivate();
      this.client = null;
    }
    console.log('[STOMP 🛑 ĐÃ NGẮT KẾT NỐI]');
  }
}
