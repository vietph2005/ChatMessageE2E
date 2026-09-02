package org.example.chat.application.chatbot;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.infrastructure.rag.RagApiClient;
import org.example.chat.presentation.dto.ChatbotResponse;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class ChatbotService {

    private final RagApiClient ragApiClient;

    public ChatbotResponse ask(String question) {
        log.info("[CHATBOT-SERVICE] Processing question: {}", question);
        return ragApiClient.ask(question);
    }
}
