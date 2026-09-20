package org.example.chat.controller;

import org.example.chat.dto.ChatMessageRequest;
import org.example.chat.entities.ChatMessage;
import org.example.chat.entities.Room;
import org.example.chat.repository.RoomRepository;
import org.springframework.messaging.handler.annotation.DestinationVariable;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.stereotype.Controller;

import java.time.LocalDateTime;

@Controller
public class ChatController {
    private final RoomRepository roomRepository;

    public ChatController(RoomRepository roomRepository) {
        this.roomRepository = roomRepository;
    }

    @MessageMapping("sendMessage/{roomId}")
    @SendTo("/topic/room/{roomId}")
    public ChatMessage sendMessage(@Payload ChatMessageRequest chatMessageRequest, @DestinationVariable String roomId) throws Exception {
        Room room = roomRepository.findByRoomId(roomId);
        if (room == null) {
            throw new Exception("Room not found: " + roomId);
        }

        ChatMessage chatMessage = new ChatMessage();
        chatMessage.setContent(chatMessageRequest.getContent());
        chatMessage.setSender(chatMessageRequest.getSender());
        chatMessage.setTimeStamp(chatMessageRequest.getLocalDateTime() != null ? chatMessageRequest.getLocalDateTime() : LocalDateTime.now());

        room.getMessages().add(chatMessage);
        roomRepository.save(room);

        return chatMessage;
    }
}
