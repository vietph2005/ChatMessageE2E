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

    @Test
    @DisplayName("Contract: POST /api/v1/conversations/{id}/handshake/accept accepts handshake")
    void testAcceptHandshakeContract() throws Exception {
        String token = jwtTokenProvider.generateToken("user_bob", "bob@gmail.com", "Bob");

        Conversation conv = Conversation.builder()
                .id("conv_999")
                .participantAId("user_alice")
                .participantBId("user_bob")
                .status(Conversation.ConversationStatus.PENDING_ACCEPTANCE)
                .build();

        HandshakeVerification handshake = HandshakeVerification.builder()
                .conversationId("conv_999")
                .layer1Status(HandshakeVerification.LayerStatus.VERIFIED)
                .layer2Status(HandshakeVerification.LayerStatus.ACCEPTED)
                .layer3Status(HandshakeVerification.LayerStatus.EXCHANGED)
                .safetyCode("842910")
                .build();

        when(handshakeService.acceptHandshake(eq("user_bob"), eq("conv_999"), eq("bob_pub_key"))).thenReturn(handshake);
        when(conversationRepository.findById("conv_999")).thenReturn(Optional.of(conv));

        ConversationDto.AcceptRequest request = new ConversationDto.AcceptRequest("bob_pub_key");

        mockMvc.perform(post("/api/v1/conversations/conv_999/handshake/accept")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value("conv_999"))
                .andExpect(jsonPath("$.handshake.layer2Status").value("ACCEPTED"))
                .andExpect(jsonPath("$.handshake.safetyCode").value("842910"));
    }

    @Test
    @DisplayName("Contract: POST /api/v1/conversations/{id}/handshake/confirm-safety-code confirms layer 4")
    void testConfirmSafetyCodeContract() throws Exception {
        String token = jwtTokenProvider.generateToken("user_alice", "alice@gmail.com", "Alice");

        Conversation conv = Conversation.builder()
                .id("conv_999")
                .participantAId("user_alice")
                .participantBId("user_bob")
                .status(Conversation.ConversationStatus.VERIFIED_ACTIVE)
                .build();

        HandshakeVerification handshake = HandshakeVerification.builder()
                .conversationId("conv_999")
                .layer4Status(HandshakeVerification.LayerStatus.CONFIRMED)
                .safetyCode("842910")
                .build();

        when(handshakeService.confirmSafetyCode(eq("user_alice"), eq("conv_999"), eq("842910"))).thenReturn(conv);
        when(handshakeService.getHandshake("conv_999")).thenReturn(handshake);

        ConversationDto.ConfirmSafetyCodeRequest request = new ConversationDto.ConfirmSafetyCodeRequest("842910");

        mockMvc.perform(post("/api/v1/conversations/conv_999/handshake/confirm-safety-code")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value("conv_999"))
                .andExpect(jsonPath("$.status").value("VERIFIED_ACTIVE"))
                .andExpect(jsonPath("$.handshake.layer4Status").value("CONFIRMED"));
    }

    @Test
    @DisplayName("Contract: POST /api/v1/conversations/{id}/handshake/re-initiate re-initiates handshake")
    void testReInitiateHandshakeContract() throws Exception {
        String token = jwtTokenProvider.generateToken("user_alice", "alice@gmail.com", "Alice");

        Conversation conv = Conversation.builder()
                .id("conv_999")
                .participantAId("user_alice")
                .participantBId("user_bob")
                .status(Conversation.ConversationStatus.HANDSHAKE_IN_PROGRESS)
                .build();

        HandshakeVerification handshake = HandshakeVerification.builder()
                .conversationId("conv_999")
                .layer1Status(HandshakeVerification.LayerStatus.VERIFIED)
                .layer2Status(HandshakeVerification.LayerStatus.ACCEPTED)
                .layer3Status(HandshakeVerification.LayerStatus.PENDING)
                .build();

        when(handshakeService.reInitiateHandshake(eq("user_alice"), eq("conv_999"), eq("new_alice_key"))).thenReturn(handshake);
        when(conversationRepository.findById("conv_999")).thenReturn(Optional.of(conv));

        ConversationDto.ReInitiateRequest request = new ConversationDto.ReInitiateRequest("new_alice_key");

        mockMvc.perform(post("/api/v1/conversations/conv_999/handshake/re-initiate")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value("conv_999"))
                .andExpect(jsonPath("$.status").value("HANDSHAKE_IN_PROGRESS"))
                .andExpect(jsonPath("$.handshake.layer3Status").value("PENDING"));
    }

    @Test
    @DisplayName("Contract: GET /api/v1/conversations/{id} returns conversation details and handshake")
    void testGetConversationDetailContract() throws Exception {
        String token = jwtTokenProvider.generateToken("user_alice", "alice@gmail.com", "Alice");

        Conversation conv = Conversation.builder()
                .id("conv_999")
                .participantAId("user_alice")
                .participantBId("user_bob")
                .status(Conversation.ConversationStatus.VERIFIED_ACTIVE)
                .build();

        HandshakeVerification handshake = HandshakeVerification.builder()
                .conversationId("conv_999")
                .layer1Status(HandshakeVerification.LayerStatus.VERIFIED)
                .layer2Status(HandshakeVerification.LayerStatus.ACCEPTED)
                .layer3Status(HandshakeVerification.LayerStatus.EXCHANGED)
                .layer4Status(HandshakeVerification.LayerStatus.CONFIRMED)
                .safetyCode("842910")
                .build();

        when(conversationRepository.findById("conv_999")).thenReturn(Optional.of(conv));
        when(handshakeService.getHandshake("conv_999")).thenReturn(handshake);

        mockMvc.perform(get("/api/v1/conversations/conv_999")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value("conv_999"))
                .andExpect(jsonPath("$.status").value("VERIFIED_ACTIVE"))
                .andExpect(jsonPath("$.handshake.safetyCode").value("842910"))
                .andExpect(jsonPath("$.handshake.layer4Status").value("CONFIRMED"));
    }
}
