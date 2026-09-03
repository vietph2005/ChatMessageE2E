package org.example.chat.unit;

import org.example.chat.application.chatbot.ChatbotService;
import org.example.chat.infrastructure.rag.RagApiClient;
import org.example.chat.presentation.dto.ChatbotResponse;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Collections;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ChatbotServiceTest {

    @Mock
    private RagApiClient ragApiClient;

    @InjectMocks
    private ChatbotService chatbotService;

    @Test
    @DisplayName("Should forward question to RagApiClient and return response")
    void shouldForwardQuestionToRagApiClient() {
        ChatbotResponse mockResponse = ChatbotResponse.builder()
                .answer("E2EE stands for End-to-End Encryption")
                .hasContext(true)
                .sources(Collections.emptyList())
                .build();

        when(ragApiClient.ask("What is E2EE?")).thenReturn(mockResponse);

        ChatbotResponse result = chatbotService.ask("What is E2EE?");

        assertNotNull(result);
        assertEquals("E2EE stands for End-to-End Encryption", result.getAnswer());
        assertTrue(result.isHasContext());
        verify(ragApiClient, times(1)).ask("What is E2EE?");
    }
}
