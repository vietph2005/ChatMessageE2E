package org.example.chat.service;

import org.example.chat.dto.ChatMessageRequest;
import org.example.chat.entities.ChatMessage;
import org.example.chat.entities.Room;

import java.util.List;

public interface RoomService {

    /**
     * Tạo phòng mới theo roomId
     * @param roomId mã định danh của phòng
     * @return Room đối tượng phòng vừa tạo
     */
    Room createRoom(String roomId);

    /**
     * Lấy thông tin phòng theo roomId
     * @param roomId mã định danh của phòng
     * @return Room đối tượng phòng hoặc null nếu không tìm thấy
     */
    Room getRoomById(String roomId);

    /**
     * Lấy danh sách tin nhắn có phân trang của một phòng
     * @param roomId mã định danh của phòng
     * @param page số trang (bắt đầu từ 0)
     * @param size số tin nhắn mỗi trang
     * @return Danh sách tin nhắn sau khi phân trang
     */
    List<ChatMessage> getMessages(String roomId, int page, int size);

    /**
     * Thêm tin nhắn mới vào phòng chat
     * @param roomId mã định danh của phòng
     * @param request dữ liệu tin nhắn gửi lên
     * @return ChatMessage tin nhắn vừa được lưu
     */
    ChatMessage addMessageToRoom(String roomId, ChatMessageRequest request);
}
