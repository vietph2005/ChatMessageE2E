package org.example.chat.integration;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.example.chat.infrastructure.rag.RagApiClient;
import org.example.chat.infrastructure.security.JwtTokenProvider;
import org.example.chat.presentation.dto.ChatbotRequest;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.HttpEntity;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.web.client.RestTemplate;

import java.util.List;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ChatbotIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @MockBean
    @Qualifier("ragRestTemplate")
    private RestTemplate ragRestTemplate;

    @Test
    @DisplayName("Integration E2E: Authenticated user queries chatbot and receives answer with citations")
    void testAuthenticatedUserQueriesChatbotSuccessfully() throws Exception {
        // Step 1: Generate valid JWT token for authenticated user
        String token = jwtTokenProvider.generateToken("user_alice_123", "alice@gmail.com", "Alice");

        // Step 2: Mock the external Python RAG microservice response
        RagApiClient.RagSourceRaw sourceRaw = new RagApiClient.RagSourceRaw(
                "faq-001",
                "E2EE Security",
                "How does 4-layer handshake protect my messages?",
                0.92
        );
        RagApiClient.RagResponseRaw rawResponse = new RagApiClient.RagResponseRaw(
                "The 4-layer handshake combines Google OAuth2, mutual consent, ECDH P-256 key exchange, and visual Safety Code confirmation.",
                List.of(sourceRaw),
                true
        );

        when(ragRestTemplate.postForObject(
                contains("/ask"),
                any(HttpEntity.class),
                eq(RagApiClient.RagResponseRaw.class)
        )).thenReturn(rawResponse);

        // Step 3: Perform HTTP request through the full filter and controller chain
        ChatbotRequest request = new ChatbotRequest("How does 4-layer handshake protect my messages?");

        mockMvc.perform(post("/api/chatbot/ask")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.answer").value(rawResponse.getAnswer()))
                .andExpect(jsonPath("$.hasContext").value(true))
                .andExpect(jsonPath("$.sources[0].id").value("faq-001"))
                .andExpect(jsonPath("$.sources[0].category").value("E2EE Security"))
                .andExpect(jsonPath("$.sources[0].similarity").value(0.92));
    }

    @Test
    @DisplayName("Integration E2E: Chatbot request validation rejects blank question with 400 Bad Request")
    void testChatbotRejectsBlankQuestion() throws Exception {
        String token = jwtTokenProvider.generateToken("user_alice_123", "alice@gmail.com", "Alice");

        ChatbotRequest invalidRequest = new ChatbotRequest("");

        mockMvc.perform(post("/api/chatbot/ask")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(invalidRequest)))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errorCode").value("VALIDATION_ERROR"));
    }
}
