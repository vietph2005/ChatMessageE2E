package org.example.chat.controller;

import org.example.chat.dto.ChatMessageRequest;
import org.example.chat.entities.ChatMessage;
import org.example.chat.service.RoomService;
import org.springframework.messaging.handler.annotation.DestinationVariable;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.stereotype.Controller;

@Controller
public class ChatController {

    private final RoomService roomService;

    public ChatController(RoomService roomService) {
        this.roomService = roomService;
    }

    @MessageMapping("sendMessage/{roomId}")
    @SendTo("/topic/room/{roomId}")
    public ChatMessage sendMessage(@Payload ChatMessageRequest chatMessageRequest, @DestinationVariable String roomId) {
        return roomService.addMessageToRoom(roomId, chatMessageRequest);
    }
}
