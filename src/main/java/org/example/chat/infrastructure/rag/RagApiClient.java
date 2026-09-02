package org.example.chat.infrastructure.rag;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.example.chat.presentation.dto.ChatbotResponse;
import org.example.chat.presentation.dto.SourceDto;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Component
public class RagApiClient {

    private final RestTemplate restTemplate;

    @Value("${rag.service.url:http://localhost:8000}")
    private String ragServiceUrl;

    public RagApiClient(@Qualifier("ragRestTemplate") RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public ChatbotResponse ask(String question) {
        String url = ragServiceUrl + "/ask";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, String> requestBody = Map.of("question", question);
        HttpEntity<Map<String, String>> entity = new HttpEntity<>(requestBody, headers);

        try {
            log.info("[RAG-CLIENT] Calling Python RAG microservice at {}", url);
            RagResponseRaw raw = restTemplate.postForObject(url, entity, RagResponseRaw.class);
            if (raw == null) {
                throw new RagApiException("RAG microservice returned empty response");
            }

            List<SourceDto> sources = raw.getSources() != null
                    ? raw.getSources().stream()
                        .map(s -> SourceDto.builder()
                                .id(s.getId())
                                .category(s.getCategory())
                                .question(s.getQuestion())
                                .similarity(s.getSimilarity())
                                .build())
                        .collect(Collectors.toList())
                    : Collections.emptyList();

            return ChatbotResponse.builder()
                    .answer(raw.getAnswer())
                    .sources(sources)
                    .hasContext(raw.isHasContext())
                    .build();

        } catch (RestClientException e) {
            log.error("[RAG-CLIENT] Error connecting to RAG microservice: {}", e.getMessage());
            throw new RagApiException("Chatbot service is temporarily unavailable: " + e.getMessage(), e);
        }
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RagResponseRaw {
        private String answer;
        private List<RagSourceRaw> sources;
        @JsonProperty("has_context")
        private boolean hasContext;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RagSourceRaw {
        private String id;
        private String category;
        private String question;
        private Double similarity;
    }
}
