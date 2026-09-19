package org.example.chat.controller;

import org.example.chat.entities.ChatMessage;
import org.example.chat.entities.Room;
import org.example.chat.repository.RoomRepository;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/rooms")
@CrossOrigin(origins = "*")
public class RoomController {
    private RoomRepository roomRepository;

    public RoomController(RoomRepository roomRepository) {
        this.roomRepository = roomRepository;
    }

    @PostMapping
    public ResponseEntity<?> createRoom(@RequestBody String roomId) {
        roomId = roomId.trim();
        if (roomId.isEmpty()) {
            return ResponseEntity.badRequest().body("Room ID cannot be empty");
        }
        if (roomRepository.findByRoomId(roomId) != null) {
            return ResponseEntity.badRequest().body("Room already exists");
        }
        Room room = new Room();
        room.setRoomId(roomId);
        roomRepository.save(room);
        return ResponseEntity.status(HttpStatus.CREATED).body(room);
    }
    @GetMapping("/{roomId}")
    public ResponseEntity<?> joinRoom(@PathVariable String roomId){
            Room room = roomRepository.findByRoomId(roomId);
            if(room == null){
                return ResponseEntity.badRequest().body("Room not found");
            }
            return ResponseEntity.ok(room);
    }
    @GetMapping("/{roomId}/messages")
    public ResponseEntity<List<ChatMessage>> getMessages(
            @PathVariable String roomId,
            @RequestParam(value = "page", defaultValue = "0") int page,
            @RequestParam(value = "size", defaultValue = "20") int size) {

        // 1. Tìm phòng theo roomId
        Room room = roomRepository.findByRoomId(roomId);
        if (room == null) {
            return ResponseEntity.badRequest().build(); // 404 Not Found
        }

        // 2. Lấy toàn bộ danh sách tin nhắn của phòng
        List<ChatMessage> allMessages = room.getMessages();
        int start = Math.max(0,allMessages.size()-(page+1)*size);
        int end = Math.min(allMessages.size(),start+size);
        List<ChatMessage> paginatedMessages = allMessages.subList(start,end);

        return ResponseEntity.ok(paginatedMessages); // 200 OK kèm dữ liệu
    }
}
