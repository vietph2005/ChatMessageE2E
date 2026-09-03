package org.example.chat.contract;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.example.chat.application.service.UserService;
import org.example.chat.domain.model.Conversation;
import org.example.chat.domain.repository.ConversationRepository;
import org.example.chat.infrastructure.security.JwtTokenProvider;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Map;
import java.util.Optional;

import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class BlockContractTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @MockBean
    private UserService userService;

    @MockBean
    private ConversationRepository conversationRepository;

    @Test
    @DisplayName("Contract: POST /api/v1/users/block blocks user and updates conversation status to BLOCKED")
    void testBlockUserContract() throws Exception {
        String token = jwtTokenProvider.generateToken("user_alice", "alice@gmail.com", "Alice");

        Conversation conv = Conversation.builder()
                .id("conv_101")
                .participantAId("user_alice")
                .participantBId("user_bob")
                .status(Conversation.ConversationStatus.VERIFIED_ACTIVE)
                .build();

        when(conversationRepository.findBetweenParticipants("user_alice", "user_bob")).thenReturn(Optional.of(conv));

        Map<String, String> body = Map.of("userId", "user_bob");

        mockMvc.perform(post("/api/v1/users/block")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(body)))
                .andExpect(status().isOk());

        verify(userService, times(1)).blockUser("user_alice", "user_bob");
        verify(conversationRepository, times(1)).save(conv);
    }

    @Test
    @DisplayName("Contract: POST /api/v1/users/unblock unblocks user and updates conversation status to VERIFIED_ACTIVE")
    void testUnblockUserContract() throws Exception {
        String token = jwtTokenProvider.generateToken("user_alice", "alice@gmail.com", "Alice");

        Conversation conv = Conversation.builder()
                .id("conv_101")
                .participantAId("user_alice")
                .participantBId("user_bob")
                .status(Conversation.ConversationStatus.BLOCKED)
                .build();

        when(conversationRepository.findBetweenParticipants("user_alice", "user_bob")).thenReturn(Optional.of(conv));

        Map<String, String> body = Map.of("userId", "user_bob");

        mockMvc.perform(post("/api/v1/users/unblock")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(body)))
                .andExpect(status().isOk());

        verify(userService, times(1)).unblockUser("user_alice", "user_bob");
        verify(conversationRepository, times(1)).save(conv);
    }
}
