package org.example.chat.presentation.controller;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.application.chatbot.ChatbotService;
import org.example.chat.presentation.dto.ChatbotRequest;
import org.example.chat.presentation.dto.ChatbotResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/api/chatbot")
@RequiredArgsConstructor
@CrossOrigin(origins = {"http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"})
public class ChatbotController {

    private final ChatbotService chatbotService;

    @PostMapping("/ask")
    public ResponseEntity<ChatbotResponse> ask(@Valid @RequestBody ChatbotRequest request) {
        log.info("[CHATBOT-CONTROLLER] Received question: {}", request.getQuestion());
        ChatbotResponse response = chatbotService.ask(request.getQuestion());
        return ResponseEntity.ok(response);
    }
}
