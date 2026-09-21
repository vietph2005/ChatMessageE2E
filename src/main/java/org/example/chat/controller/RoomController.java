package org.example.chat.controller;

import org.example.chat.common.response.ApiResponse;
import org.example.chat.entities.ChatMessage;
import org.example.chat.entities.Room;
import org.example.chat.service.RoomService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/rooms")
public class RoomController {

    private final RoomService roomService;

    public RoomController(RoomService roomService) {
        this.roomService = roomService;
    }

    @PostMapping
    public ResponseEntity<ApiResponse<Room>> createRoom(@RequestBody String roomId) {
        Room room = roomService.createRoom(roomId);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success("Tạo phòng thành công", room));
    }

    @GetMapping("/{roomId}")
    public ResponseEntity<ApiResponse<Room>> joinRoom(@PathVariable String roomId) {
        Room room = roomService.getRoomById(roomId);
        if (room == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(ApiResponse.error("ROOM_NOT_FOUND", "Phòng không tồn tại"));
        }
        return ResponseEntity.ok(ApiResponse.success("Tham gia phòng thành công", room));
    }

    @GetMapping("/{roomId}/messages")
    public ResponseEntity<ApiResponse<List<ChatMessage>>> getMessages(
            @PathVariable String roomId,
            @RequestParam(value = "page", defaultValue = "0") int page,
            @RequestParam(value = "size", defaultValue = "20") int size) {

        List<ChatMessage> paginatedMessages = roomService.getMessages(roomId, page, size);
        if (paginatedMessages == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(ApiResponse.error("ROOM_NOT_FOUND", "Phòng không tồn tại"));
        }
        return ResponseEntity.ok(ApiResponse.success(paginatedMessages));
    }
}
