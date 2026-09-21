package org.example.chat.service.impl;

import org.example.chat.dto.ChatMessageRequest;
import org.example.chat.entities.ChatMessage;
import org.example.chat.entities.Room;
import org.example.chat.repository.RoomRepository;
import org.example.chat.service.RoomService;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class RoomServiceImpl implements RoomService {

    private final RoomRepository roomRepository;

    public RoomServiceImpl(RoomRepository roomRepository) {
        this.roomRepository = roomRepository;
    }

    @Override
    public Room createRoom(String roomId) {
        roomId = roomId.trim();
        if (roomId.isEmpty()) {
            throw new IllegalArgumentException("Room ID cannot be empty");
        }
        if (roomRepository.findByRoomId(roomId) != null) {
            throw new IllegalArgumentException("Room already exists");
        }

        Room room = new Room();
        room.setRoomId(roomId);
        return roomRepository.save(room);
    }

    @Override
    public Room getRoomById(String roomId) {
        return roomRepository.findByRoomId(roomId);
    }

    @Override
    public List<ChatMessage> getMessages(String roomId, int page, int size) {
        Room room = roomRepository.findByRoomId(roomId);
        if (room == null) {
            return null;
        }

        List<ChatMessage> allMessages = room.getMessages();
        int start = Math.max(0, allMessages.size() - (page + 1) * size);
        int end = Math.min(allMessages.size(), start + size);
        return allMessages.subList(start, end);
    }

    @Override
    public ChatMessage addMessageToRoom(String roomId, ChatMessageRequest request) {
        Room room = roomRepository.findByRoomId(roomId);
        if (room == null) {
            throw new IllegalArgumentException("Room not found: " + roomId);
        }

        ChatMessage chatMessage = new ChatMessage();
        chatMessage.setContent(request.getContent());
        chatMessage.setSender(request.getSender());
        chatMessage.setTimeStamp(request.getLocalDateTime() != null ? request.getLocalDateTime() : LocalDateTime.now());

        room.getMessages().add(chatMessage);
        roomRepository.save(room);

        return chatMessage;
    }
}
