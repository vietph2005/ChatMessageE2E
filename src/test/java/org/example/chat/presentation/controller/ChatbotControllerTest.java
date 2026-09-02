package org.example.chat.presentation.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.example.chat.application.chatbot.ChatbotService;
import org.example.chat.presentation.dto.ChatbotRequest;
import org.example.chat.presentation.dto.ChatbotResponse;
import org.example.chat.presentation.dto.SourceDto;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ChatbotControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private ChatbotService chatbotService;

    @Test
    @DisplayName("POST /api/chatbot/ask returns 200 and chatbot response with sources")
    void testAskSuccess() throws Exception {
        ChatbotResponse mockResponse = ChatbotResponse.builder()
                .answer("Để tìm bạn bè, hãy nhập email vào thanh tìm kiếm.")
                .sources(List.of(
                        SourceDto.builder()
                                .id("search-001_c00")
                                .category("Tìm kiếm")
                                .question("Làm sao tìm bạn bè?")
                                .similarity(0.88)
                                .build()
                ))
                .hasContext(true)
                .build();

        when(chatbotService.ask(anyString())).thenReturn(mockResponse);

        ChatbotRequest request = ChatbotRequest.builder()
                .question("Làm sao tìm bạn bè?")
                .build();

        mockMvc.perform(post("/api/chatbot/ask")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.answer").value("Để tìm bạn bè, hãy nhập email vào thanh tìm kiếm."))
                .andExpect(jsonPath("$.hasContext").value(true))
                .andExpect(jsonPath("$.sources[0].category").value("Tìm kiếm"));
    }

    @Test
    @DisplayName("POST /api/chatbot/ask with blank question returns 400 Bad Request")
    void testAskBlankQuestionReturnsBadRequest() throws Exception {
        ChatbotRequest request = ChatbotRequest.builder()
                .question("   ")
                .build();

        mockMvc.perform(post("/api/chatbot/ask")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isBadRequest());
    }
}
