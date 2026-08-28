package org.example.chat.contract;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.example.chat.application.service.HandshakeService;
import org.example.chat.application.service.UserService;
import org.example.chat.domain.model.Conversation;
import org.example.chat.domain.model.HandshakeVerification;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.domain.repository.ConversationRepository;
import org.example.chat.infrastructure.security.JwtTokenProvider;
import org.example.chat.presentation.dto.ConversationDto;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;
import java.util.Optional;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class HandshakeContractTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @MockBean
    private HandshakeService handshakeService;

    @MockBean
    private ConversationRepository conversationRepository;

    @MockBean
    private UserService userService;

    @Test
    @DisplayName("Contract: POST /api/v1/conversations initiates 4-layer handshake")
    void testInitiateConversationContract() throws Exception {
        String token = jwtTokenProvider.generateToken("user_alice", "alice@gmail.com", "Alice");

        Conversation conv = Conversation.builder()
                .id("conv_999")
                .participantAId("user_alice")
                .participantBId("user_bob")
                .status(Conversation.ConversationStatus.PENDING_ACCEPTANCE)
                .build();

        HandshakeVerification handshake = HandshakeVerification.builder()
                .conversationId("conv_999")
                .layer1Status(HandshakeVerification.LayerStatus.VERIFIED)
                .layer2Status(HandshakeVerification.LayerStatus.PENDING)
                .build();

        when(handshakeService.initiateHandshake(eq("user_alice"), eq("bob@gmail.com"), any())).thenReturn(conv);
        when(handshakeService.getHandshake("conv_999")).thenReturn(handshake);

        ConversationDto.InitiateRequest request = ConversationDto.InitiateRequest.builder()
                .recipientEmail("bob@gmail.com")
                .initiatorPublicKey("mock_key_spki")
                .build();

        mockMvc.perform(post("/api/v1/conversations")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.id").value("conv_999"))
                .andExpect(jsonPath("$.status").value("PENDING_ACCEPTANCE"))
                .andExpect(jsonPath("$.handshake.layer1Status").value("VERIFIED"));
    }

    @Test
    @DisplayName("Contract: GET /api/v1/conversations returns list of summaries with peer users")
    void testListConversationsContract() throws Exception {
        String token = jwtTokenProvider.generateToken("user_alice", "alice@gmail.com", "Alice");

        Conversation conv = Conversation.builder()
                .id("conv_999")
                .participantAId("user_alice")
                .participantBId("user_bob")
                .status(Conversation.ConversationStatus.VERIFIED_ACTIVE)
                .lastMessageSnippet("Encrypted preview")
                .build();

        UserProfile bob = UserProfile.builder()
                .id("user_bob")
                .email("bob@gmail.com")
                .displayName("Bob")
                .isOnline(true)
                .build();

        when(conversationRepository.findUserConversations("user_alice")).thenReturn(List.of(conv));
        when(userService.getUserById("user_bob")).thenReturn(bob);

        mockMvc.perform(get("/api/v1/conversations")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].id").value("conv_999"))
                .andExpect(jsonPath("$[0].peerUser.email").value("bob@gmail.com"))
                .andExpect(jsonPath("$[0].status").value("VERIFIED_ACTIVE"));
    }
}
