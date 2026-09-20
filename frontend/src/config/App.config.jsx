/**
 * Cấu hình hệ thống kết nối Backend
 * Dễ dàng chuyển đổi giữa môi trường Local Development và Production khi Deploy
 * thông qua biến môi trường (.env / VITE_API_BASE_URL).
 */

// Đường dẫn gốc của Backend API (mặc định http://localhost:8080 nếu chưa có biến môi trường)
export const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

// Đường dẫn kết nối WebSocket STOMP
export const wsURL = import.meta.env.VITE_WS_URL || 'ws://localhost:8080/ws';
