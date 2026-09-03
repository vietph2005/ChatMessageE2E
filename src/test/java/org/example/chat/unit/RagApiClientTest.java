package org.example.chat.unit;

import org.example.chat.infrastructure.rag.RagApiClient;
import org.example.chat.infrastructure.rag.RagApiException;
import org.example.chat.presentation.dto.ChatbotResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.HttpEntity;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class RagApiClientTest {

    @Mock
    private RestTemplate restTemplate;

    private RagApiClient ragApiClient;

    @BeforeEach
    void setUp() {
        ragApiClient = new RagApiClient(restTemplate);
        ReflectionTestUtils.setField(ragApiClient, "ragServiceUrl", "http://localhost:8000");
    }

    @Test
    @DisplayName("Should successfully call RAG service and map response to ChatbotResponse")
    void shouldReturnChatbotResponseOnSuccessfulCall() {
        // 1. Arrange
        RagApiClient.RagSourceRaw sourceRaw = new RagApiClient.RagSourceRaw(
                "src_1", "security", "What is E2EE?", 0.95
        );
        RagApiClient.RagResponseRaw responseRaw = new RagApiClient.RagResponseRaw(
                "E2EE stands for End-to-End Encryption.",
                List.of(sourceRaw),
                true
        );

        when(restTemplate.postForObject(
                eq("http://localhost:8000/ask"),
                any(HttpEntity.class),
                eq(RagApiClient.RagResponseRaw.class)
        )).thenReturn(responseRaw);

        // 2. Act
        ChatbotResponse result = ragApiClient.ask("What is E2EE?");

        // 3. Assert
        assertNotNull(result);
        assertEquals("E2EE stands for End-to-End Encryption.", result.getAnswer());
        assertTrue(result.isHasContext());
        assertEquals(1, result.getSources().size());
        assertEquals("src_1", result.getSources().get(0).getId());
        assertEquals("security", result.getSources().get(0).getCategory());
        assertEquals(0.95, result.getSources().get(0).getSimilarity());

        // Verify request payload
        ArgumentCaptor<HttpEntity<Map<String, String>>> entityCaptor = ArgumentCaptor.forClass(HttpEntity.class);
        verify(restTemplate, times(1)).postForObject(eq("http://localhost:8000/ask"), entityCaptor.capture(), eq(RagApiClient.RagResponseRaw.class));
        assertEquals("What is E2EE?", entityCaptor.getValue().getBody().get("question"));
    }

    @Test
    @DisplayName("Should handle null sources gracefully without throwing NullPointerException")
    void shouldHandleNullSourcesGracefully() {
        // 1. Arrange
        RagApiClient.RagResponseRaw responseRaw = new RagApiClient.RagResponseRaw(
                "General response without specific sources.",
                null,
                false
        );

        when(restTemplate.postForObject(anyString(), any(), eq(RagApiClient.RagResponseRaw.class)))
                .thenReturn(responseRaw);

        // 2. Act
        ChatbotResponse result = ragApiClient.ask("General query");

        // 3. Assert
        assertNotNull(result);
        assertEquals("General response without specific sources.", result.getAnswer());
        assertFalse(result.isHasContext());
        assertNotNull(result.getSources());
        assertTrue(result.getSources().isEmpty());
    }

    @Test
    @DisplayName("Should throw RagApiException when RAG microservice returns empty/null body")
    void shouldThrowRagApiExceptionWhenResponseBodyIsNull() {
        // 1. Arrange
        when(restTemplate.postForObject(anyString(), any(), eq(RagApiClient.RagResponseRaw.class)))
                .thenReturn(null);

        // 2 & 3. Act & Assert
        RagApiException exception = assertThrows(RagApiException.class, () -> {
            ragApiClient.ask("Any question");
        });

        assertTrue(exception.getMessage().contains("empty response"));
    }

    @Test
    @DisplayName("Should throw RagApiException when RestTemplate throws RestClientException (network/timeout error)")
    void shouldThrowRagApiExceptionOnNetworkError() {
        // 1. Arrange
        when(restTemplate.postForObject(anyString(), any(), eq(RagApiClient.RagResponseRaw.class)))
                .thenThrow(new RestClientException("Connection refused"));

        // 2 & 3. Act & Assert
        RagApiException exception = assertThrows(RagApiException.class, () -> {
            ragApiClient.ask("Any question");
        });

        assertTrue(exception.getMessage().contains("temporarily unavailable"));
        assertTrue(exception.getMessage().contains("Connection refused"));
    }
}
