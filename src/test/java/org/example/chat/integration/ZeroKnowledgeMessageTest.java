package org.example.chat.integration;

import org.example.chat.application.service.MessageService;
import org.example.chat.domain.exception.DomainException;
import org.example.chat.domain.model.Conversation;
import org.example.chat.domain.model.EncryptedMessage;
import org.example.chat.domain.repository.ConversationRepository;
import org.example.chat.domain.repository.MessageRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class ZeroKnowledgeMessageTest {

    @Mock
    private MessageRepository messageRepository;

    @Mock
    private ConversationRepository conversationRepository;

    @InjectMocks
    private MessageService messageService;

    @Test
    @DisplayName("Zero-Knowledge Invariant: System strictly blocks sending to unverified conversations")
    void shouldBlockMessagingInUnverifiedConversation() {
        Conversation pendingConv = Conversation.builder()
                .id("conv_unverified")
                .participantAId("alice")
                .participantBId("bob")
                .status(Conversation.ConversationStatus.PENDING_ACCEPTANCE)
                .build();

        when(conversationRepository.findById("conv_unverified")).thenReturn(Optional.of(pendingConv));

        assertThrows(DomainException.class, () ->
                messageService.sendEncryptedMessage(
                        "alice",
                        "conv_unverified",
                        "bob",
                        EncryptedMessage.MessageType.TEXT,
                        "encrypted_ciphertext_base64",
                        "iv_base64",
                        null
                ));
    }

    @Test
    @DisplayName("Zero-Knowledge Invariant: Persisted message strictly contains ciphertext, zero plaintext")
    void shouldPersistEncryptedCiphertextOnly() {
        Conversation verifiedConv = Conversation.builder()
                .id("conv_verified")
                .participantAId("alice")
                .participantBId("bob")
                .status(Conversation.ConversationStatus.VERIFIED_ACTIVE)
                .build();

        when(conversationRepository.findById("conv_verified")).thenReturn(Optional.of(verifiedConv));
        when(messageRepository.countByConversationId("conv_verified")).thenReturn(0);
        when(messageRepository.save(any(EncryptedMessage.class))).thenAnswer(i -> {
            EncryptedMessage m = i.getArgument(0);
            m.setId("msg_001");
            return m;
        });

        String ciphertext = "U2FsdGVkX1+vupppZks=";
        String iv = "123456789012";

        EncryptedMessage result = messageService.sendEncryptedMessage(
                "alice",
                "conv_verified",
                "bob",
                EncryptedMessage.MessageType.TEXT,
                ciphertext,
                iv,
                null
        );

        assertNotNull(result);
        assertEquals(ciphertext, result.getCiphertext());
        assertEquals(iv, result.getInitializationVector());
        assertEquals(1, result.getSequenceNumber());
        assertFalse(result.isRevoked());
    }
}
