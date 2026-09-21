import { Room } from '../types';
import { baseURL } from '../config/App.config';

// Đường dẫn API phòng chat sử dụng baseURL dùng chung
const ROOM_API_URL = `${baseURL}/api/v1/rooms`;

/**
 * Gọi API tạo phòng chat mới
 * @param roomId Mã phòng cần tạo
 * @returns Room thông tin phòng vừa tạo
 */
export const createRoomApi = async (roomId: string): Promise<Room> => {
  const trimmedId = roomId.trim();
  const response = await fetch(ROOM_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'text/plain',
    },
    body: trimmedId,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const errorMsg = errorData?.message || 'Không thể tạo phòng chat. Vui lòng thử lại.';
    throw new Error(errorMsg);
  }

  const result = await response.json();
  return result?.data ? result.data : result;
};

/**
 * Gọi API kiểm tra và tham gia phòng chat hiện có
 * @param roomId Mã phòng cần tham gia
 * @returns Room thông tin phòng
 */
export const joinRoomApi = async (roomId: string): Promise<Room> => {
  const trimmedId = roomId.trim();
  const response = await fetch(`${ROOM_API_URL}/${encodeURIComponent(trimmedId)}`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const errorMsg = errorData?.message || 'Phòng không tồn tại hoặc đã xảy ra lỗi.';
    throw new Error(errorMsg);
  }

  const result = await response.json();
  return result?.data ? result.data : result;
};
