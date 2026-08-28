package org.example.chat.unit;

import org.example.chat.application.service.HandshakeService;
import org.example.chat.domain.exception.DomainException;
import org.example.chat.domain.model.Conversation;
import org.example.chat.domain.model.HandshakeVerification;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.domain.repository.ConversationRepository;
import org.example.chat.domain.repository.HandshakeRepository;
import org.example.chat.domain.repository.UserRepository;
import org.example.chat.presentation.websocket.HandshakeNotificationHandler;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class HandshakeServiceTest {

    @Mock
    private ConversationRepository conversationRepository;

    @Mock
    private HandshakeRepository handshakeRepository;

    @Mock
    private UserRepository userRepository;

    @Mock
    private HandshakeNotificationHandler notificationHandler;

    private HandshakeService handshakeService;

    @BeforeEach
    void setUp() {
        handshakeService = new HandshakeService(conversationRepository, handshakeRepository, userRepository, notificationHandler);
    }

    @Test
    @DisplayName("Should successfully execute 4-layer asynchronous handshake lifecycle")
    void shouldExecute4LayerHandshake() {
        UserProfile initiator = UserProfile.builder().id("user_alice").email("alice@gmail.com").build();
        UserProfile recipient = UserProfile.builder().id("user_bob").email("bob@gmail.com").build();

        when(userRepository.findByEmail("bob@gmail.com")).thenReturn(Optional.of(recipient));
        when(userRepository.findById("user_alice")).thenReturn(Optional.of(initiator));
        when(conversationRepository.findBetweenParticipants("user_alice", "user_bob")).thenReturn(Optional.empty());

        Conversation conv = Conversation.builder()
                .id("conv_123")
                .participantAId("user_alice")
                .participantBId("user_bob")
                .status(Conversation.ConversationStatus.PENDING_ACCEPTANCE)
                .build();
        when(conversationRepository.save(any(Conversation.class))).thenReturn(conv);

        // Step 1: Initiate (Layer 1 verified, Layer 2 pending)
        Conversation initiated = handshakeService.initiateHandshake("user_alice", "bob@gmail.com", "alice_pub_key_base64");
        assertNotNull(initiated);
        assertEquals(Conversation.ConversationStatus.PENDING_ACCEPTANCE, initiated.getStatus());
        verify(handshakeRepository).save(any(HandshakeVerification.class));

        // Step 2: Accept Handshake (Layer 2 accepted, Layer 3 pre-key exchanged, Layer 4 challenge computed)
        HandshakeVerification handshake = HandshakeVerification.builder()
                .conversationId("conv_123")
                .initiatorId("user_alice")
                .recipientId("user_bob")
                .initiatorPublicKey("alice_pub_key_base64")
                .layer1Status(HandshakeVerification.LayerStatus.VERIFIED)
                .layer2Status(HandshakeVerification.LayerStatus.PENDING)
                .build();

        when(conversationRepository.findById("conv_123")).thenReturn(Optional.of(conv));
        when(handshakeRepository.findByConversationId("conv_123")).thenReturn(Optional.of(handshake));
        when(handshakeRepository.save(any(HandshakeVerification.class))).thenAnswer(invocation -> invocation.getArgument(0));

        HandshakeVerification accepted = handshakeService.acceptHandshake("user_bob", "conv_123", "bob_pub_key_base64");
        assertEquals(HandshakeVerification.LayerStatus.ACCEPTED, accepted.getLayer2Status());
        assertEquals(HandshakeVerification.LayerStatus.EXCHANGED, accepted.getLayer3Status());
        assertEquals(HandshakeVerification.LayerStatus.PENDING, accepted.getLayer4Status());
        assertNotNull(accepted.getSafetyCode());
        assertEquals(6, accepted.getSafetyCode().length());

        // Step 3: Confirm Safety Code (Layer 4 confirmed -> VERIFIED_ACTIVE)
        Conversation activeConv = Conversation.builder()
                .id("conv_123")
                .participantAId("user_alice")
                .participantBId("user_bob")
                .status(Conversation.ConversationStatus.VERIFIED_ACTIVE)
                .build();
        when(conversationRepository.save(any(Conversation.class))).thenReturn(activeConv);

        Conversation verified = handshakeService.confirmSafetyCode("user_bob", "conv_123", accepted.getSafetyCode());
        assertEquals(Conversation.ConversationStatus.VERIFIED_ACTIVE, verified.getStatus());
    }

    @Test
    @DisplayName("Should throw DomainException on safety code mismatch")
    void shouldRejectInvalidSafetyCode() {
        Conversation conv = Conversation.builder().id("conv_123").status(Conversation.ConversationStatus.HANDSHAKE_IN_PROGRESS).build();
        HandshakeVerification handshake = HandshakeVerification.builder()
                .conversationId("conv_123")
                .safetyCode("842910")
                .build();

        when(conversationRepository.findById("conv_123")).thenReturn(Optional.of(conv));
        when(handshakeRepository.findByConversationId("conv_123")).thenReturn(Optional.of(handshake));

        assertThrows(DomainException.class, () ->
                handshakeService.confirmSafetyCode("user_bob", "conv_123", "000000"));
    }
}
