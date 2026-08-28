package org.example.chat.integration;

import org.example.chat.application.service.HandshakeService;
import org.example.chat.application.service.MessageService;
import org.example.chat.application.service.UserService;
import org.example.chat.domain.model.Conversation;
import org.example.chat.domain.model.EncryptedMessage;
import org.example.chat.domain.model.HandshakeVerification;
import org.example.chat.domain.model.UserProfile;
import org.example.chat.domain.repository.ConversationRepository;
import org.example.chat.domain.repository.HandshakeRepository;
import org.example.chat.domain.repository.MessageRepository;
import org.example.chat.domain.repository.UserRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;

import java.time.Instant;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@SpringBootTest
class FullEndToEndChatIntegrationTest {

    @Autowired
    private UserService userService;

    @Autowired
    private HandshakeService handshakeService;

    @Autowired
    private MessageService messageService;

    @MockBean
    private UserRepository userRepository;

    @MockBean
    private ConversationRepository conversationRepository;

    @MockBean
    private HandshakeRepository handshakeRepository;

    @MockBean
    private MessageRepository messageRepository;

    @Test
    @DisplayName("Complete E2E Lifecycle: Auth -> 4-Layer Handshake -> E2EE Encrypted Message -> Unsend")
    void testCompleteE2EChatLifecycle() {
        // Step 1: User Auth Setup
        UserProfile alice = UserProfile.builder()
                .id("user_alice_id")
                .googleSubjectId("sub-alice")
                .email("alice@gmail.com")
                .displayName("Alice")
                .isOnline(true)
                .build();

        UserProfile bob = UserProfile.builder()
                .id("user_bob_id")
                .googleSubjectId("sub-bob")
                .email("bob@gmail.com")
                .displayName("Bob")
                .isOnline(true)
                .build();

        when(userRepository.findById("user_alice_id")).thenReturn(Optional.of(alice));
        when(userRepository.findById("user_bob_id")).thenReturn(Optional.of(bob));
        when(userRepository.findByEmail("bob@gmail.com")).thenReturn(Optional.of(bob));
        when(userRepository.findByGoogleSubjectId("sub-alice")).thenReturn(Optional.of(alice));
        when(userRepository.save(any(UserProfile.class))).thenAnswer(i -> i.getArgument(0));

        // Step 2: Layer 1 & 2 - Alice initiates handshake while Bob is offline
        Conversation conv = Conversation.builder()
                .id("conv_e2e_101")
                .participantAId("user_alice_id")
                .participantBId("user_bob_id")
                .status(Conversation.ConversationStatus.PENDING_ACCEPTANCE)
                .createdAt(Instant.now())
                .build();

        HandshakeVerification handshake = HandshakeVerification.builder()
                .conversationId("conv_e2e_101")
                .initiatorId("user_alice_id")
                .recipientId("user_bob_id")
                .initiatorPublicKey("ALICE_PUB_KEY_SPKI")
                .layer1Status(HandshakeVerification.LayerStatus.VERIFIED)
                .layer2Status(HandshakeVerification.LayerStatus.PENDING)
                .build();

        when(conversationRepository.findBetweenParticipants("user_alice_id", "user_bob_id")).thenReturn(Optional.empty());
        when(conversationRepository.save(any(Conversation.class))).thenAnswer(i -> {
            Conversation c = i.getArgument(0);
            c.setId("conv_e2e_101");
            return c;
        });
        when(conversationRepository.findById("conv_e2e_101")).thenReturn(Optional.of(conv));
        when(handshakeRepository.findByConversationId("conv_e2e_101")).thenReturn(Optional.of(handshake));
        when(handshakeRepository.save(any(HandshakeVerification.class))).thenAnswer(i -> i.getArgument(0));

        Conversation initiated = handshakeService.initiateHandshake("user_alice_id", "bob@gmail.com", "ALICE_PUB_KEY_SPKI");
        assertEquals(Conversation.ConversationStatus.PENDING_ACCEPTANCE, initiated.getStatus());

        // Step 3: Layer 2 & 3 - Bob logs in and accepts handshake
        HandshakeVerification accepted = handshakeService.acceptHandshake("user_bob_id", "conv_e2e_101", "BOB_PUB_KEY_SPKI");
        assertEquals(HandshakeVerification.LayerStatus.ACCEPTED, accepted.getLayer2Status());
        assertEquals(HandshakeVerification.LayerStatus.EXCHANGED, accepted.getLayer3Status());
        assertNotNull(accepted.getSafetyCode());

        // Step 4: Layer 4 - Confirm Safety Code match -> Channel is now VERIFIED_ACTIVE
        conv.setStatus(Conversation.ConversationStatus.VERIFIED_ACTIVE);
        Conversation active = handshakeService.confirmSafetyCode("user_alice_id", "conv_e2e_101", accepted.getSafetyCode());
        assertEquals(Conversation.ConversationStatus.VERIFIED_ACTIVE, active.getStatus());

        // Step 5: Encrypted Message Transmission
        EncryptedMessage msg = EncryptedMessage.builder()
                .id("msg_e2e_1")
                .conversationId("conv_e2e_101")
                .senderId("user_alice_id")
                .recipientId("user_bob_id")
                .messageType(EncryptedMessage.MessageType.TEXT)
                .ciphertext("ZW5jcnlwdGVkX2Jhc2U2NF9wYXlsb2Fk")
                .initializationVector("aXYxMjM0NTY3ODkw")
                .sequenceNumber(1)
                .sentAt(Instant.now())
                .isRevoked(false)
                .build();

        when(messageRepository.countByConversationId("conv_e2e_101")).thenReturn(0);
        when(messageRepository.save(any(EncryptedMessage.class))).thenReturn(msg);
        when(messageRepository.findById("msg_e2e_1")).thenReturn(Optional.of(msg));

        EncryptedMessage sent = messageService.sendEncryptedMessage(
                "user_alice_id", "conv_e2e_101", "user_bob_id",
                EncryptedMessage.MessageType.TEXT,
                "ZW5jcnlwdGVkX2Jhc2U2NF9wYXlsb2Fk",
                "aXYxMjM0NTY3ODkw",
                null
        );

        assertEquals("ZW5jcnlwdGVkX2Jhc2U2NF9wYXlsb2Fk", sent.getCiphertext());
        assertFalse(sent.isRevoked());

        // Step 6: Unsend Message for Everyone
        EncryptedMessage revoked = messageService.revokeMessage("user_alice_id", "conv_e2e_101", "msg_e2e_1");
        assertTrue(revoked.isRevoked());
        assertEquals("UNSENT_TOMBSTONE", revoked.getCiphertext());
    }
}
