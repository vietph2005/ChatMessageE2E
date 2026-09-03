package org.example.chat.unit;

import org.example.chat.application.service.MessageService;
import org.example.chat.domain.exception.DomainException;
import org.example.chat.domain.model.Conversation;
import org.example.chat.domain.model.EncryptedMessage;
import org.example.chat.domain.repository.ConversationRepository;
import org.example.chat.domain.repository.MessageRepository;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class MessageServiceTest {

    @Mock
    private MessageRepository messageRepository;

    @Mock
    private ConversationRepository conversationRepository;

    @InjectMocks
    private MessageService messageService;

    @Nested
    @DisplayName("sendEncryptedMessage tests")
    class SendEncryptedMessageTests {

        @Test
        @DisplayName("Should send encrypted text message successfully and update conversation metadata")
        void shouldSendTextMessageSuccessfully() {
            Conversation conv = Conversation.builder()
                    .id("conv_100")
                    .participantAId("user_alice")
                    .participantBId("user_bob")
                    .status(Conversation.ConversationStatus.VERIFIED_ACTIVE)
                    .build();

            when(conversationRepository.findById("conv_100")).thenReturn(Optional.of(conv));
            when(messageRepository.countByConversationId("conv_100")).thenReturn(2);
            when(messageRepository.save(any(EncryptedMessage.class))).thenAnswer(i -> {
                EncryptedMessage m = i.getArgument(0);
                m.setId("msg_generated_id");
                return m;
            });

            EncryptedMessage sent = messageService.sendEncryptedMessage(
                    "user_alice",
                    "conv_100",
                    "user_bob",
                    EncryptedMessage.MessageType.TEXT,
                    "CIPHERTEXT_BASE64",
                    "IV_BASE64",
                    null
            );

            assertNotNull(sent);
            assertEquals("msg_generated_id", sent.getId());
            assertEquals("CIPHERTEXT_BASE64", sent.getCiphertext());
            assertEquals("IV_BASE64", sent.getInitializationVector());
            assertEquals(3, sent.getSequenceNumber());
            assertFalse(sent.isRevoked());

            verify(conversationRepository, times(1)).save(conv);
            assertEquals("msg_generated_id", conv.getLastMessageId());
            assertEquals("[Encrypted Message]", conv.getLastMessageSnippet());
        }

        @Test
        @DisplayName("Should send encrypted image message and set last message snippet accordingly")
        void shouldSendImageMessageSuccessfully() {
            Conversation conv = Conversation.builder()
                    .id("conv_100")
                    .participantAId("user_alice")
                    .participantBId("user_bob")
                    .status(Conversation.ConversationStatus.VERIFIED_ACTIVE)
                    .build();

            when(conversationRepository.findById("conv_100")).thenReturn(Optional.of(conv));
            when(messageRepository.countByConversationId("conv_100")).thenReturn(0);
            when(messageRepository.save(any(EncryptedMessage.class))).thenAnswer(i -> {
                EncryptedMessage m = i.getArgument(0);
                m.setId("msg_img_01");
                return m;
            });

            EncryptedMessage sent = messageService.sendEncryptedMessage(
                    "user_alice",
                    "conv_100",
                    "user_bob",
                    EncryptedMessage.MessageType.IMAGE,
                    "CIPHERTEXT_IMG",
                    "IV_IMG",
                    "https://storage.com/enc-img.bin"
            );

            assertNotNull(sent);
            assertEquals(EncryptedMessage.MessageType.IMAGE, sent.getMessageType());
            assertEquals("[Encrypted Image]", conv.getLastMessageSnippet());
        }

        @Test
        @DisplayName("Should throw DomainException when conversation does not exist")
        void shouldThrowWhenConversationNotFound() {
            when(conversationRepository.findById("invalid_conv")).thenReturn(Optional.empty());

            DomainException ex = assertThrows(DomainException.class, () ->
                    messageService.sendEncryptedMessage(
                            "user_alice", "invalid_conv", "user_bob",
                            EncryptedMessage.MessageType.TEXT, "cip", "iv", null
                    ));

            assertEquals("CONVERSATION_NOT_FOUND", ex.getErrorCode());
        }

        @Test
        @DisplayName("Should throw DomainException when conversation is not verified active")
        void shouldThrowWhenConversationNotVerified() {
            Conversation unverified = Conversation.builder()
                    .id("conv_pending")
                    .participantAId("user_alice")
                    .participantBId("user_bob")
                    .status(Conversation.ConversationStatus.PENDING_ACCEPTANCE)
                    .build();

            when(conversationRepository.findById("conv_pending")).thenReturn(Optional.of(unverified));

            DomainException ex = assertThrows(DomainException.class, () ->
                    messageService.sendEncryptedMessage(
                            "user_alice", "conv_pending", "user_bob",
                            EncryptedMessage.MessageType.TEXT, "cip", "iv", null
                    ));

            assertEquals("UNVERIFIED_CONVERSATION", ex.getErrorCode());
        }

        @Test
        @DisplayName("Should throw DomainException when sender is not a participant")
        void shouldThrowWhenSenderUnauthorized() {
            Conversation conv = Conversation.builder()
                    .id("conv_100")
                    .participantAId("user_alice")
                    .participantBId("user_bob")
                    .status(Conversation.ConversationStatus.VERIFIED_ACTIVE)
                    .build();

            when(conversationRepository.findById("conv_100")).thenReturn(Optional.of(conv));

            DomainException ex = assertThrows(DomainException.class, () ->
                    messageService.sendEncryptedMessage(
                            "user_stranger", "conv_100", "user_bob",
                            EncryptedMessage.MessageType.TEXT, "cip", "iv", null
                    ));

            assertEquals("UNAUTHORIZED_SENDER", ex.getErrorCode());
        }
    }

    @Nested
    @DisplayName("revokeMessage tests")
    class RevokeMessageTests {

        @Test
        @DisplayName("Should unsend message for everyone when caller is the sender")
        void shouldRevokeMessageSuccessfully() {
            EncryptedMessage original = EncryptedMessage.builder()
                    .id("msg_001")
                    .conversationId("conv_100")
                    .senderId("user_alice")
                    .recipientId("user_bob")
                    .ciphertext("SECRET_CIPHERTEXT")
                    .mediaUrl("https://storage.com/secret.png")
                    .isRevoked(false)
                    .build();

            when(messageRepository.findById("msg_001")).thenReturn(Optional.of(original));
            when(messageRepository.save(any(EncryptedMessage.class))).thenAnswer(i -> i.getArgument(0));

            EncryptedMessage revoked = messageService.revokeMessage("user_alice", "conv_100", "msg_001");

            assertTrue(revoked.isRevoked());
            assertEquals("UNSENT_TOMBSTONE", revoked.getCiphertext());
            assertNull(revoked.getMediaUrl());
            assertNotNull(revoked.getRevokedAt());
            verify(messageRepository, times(1)).save(original);
        }

        @Test
        @DisplayName("Should throw DomainException when message does not exist")
        void shouldThrowWhenMessageNotFound() {
            when(messageRepository.findById("invalid_msg")).thenReturn(Optional.empty());

            DomainException ex = assertThrows(DomainException.class, () ->
                    messageService.revokeMessage("user_alice", "conv_100", "invalid_msg"));

            assertEquals("MESSAGE_NOT_FOUND", ex.getErrorCode());
        }

        @Test
        @DisplayName("Should throw DomainException when non-sender tries to unsend message")
        void shouldThrowWhenNonSenderTriesToRevoke() {
            EncryptedMessage original = EncryptedMessage.builder()
                    .id("msg_001")
                    .conversationId("conv_100")
                    .senderId("user_alice")
                    .recipientId("user_bob")
                    .ciphertext("SECRET_CIPHERTEXT")
                    .build();

            when(messageRepository.findById("msg_001")).thenReturn(Optional.of(original));

            DomainException ex = assertThrows(DomainException.class, () ->
                    messageService.revokeMessage("user_bob", "conv_100", "msg_001"));

            assertEquals("UNAUTHORIZED_REVOCATION", ex.getErrorCode());
        }
    }

    @Nested
    @DisplayName("getConversationMessages tests")
    class GetConversationMessagesTests {

        @Test
        @DisplayName("Should return message list when requester is a participant")
        void shouldReturnMessagesForParticipant() {
            Conversation conv = Conversation.builder()
                    .id("conv_100")
                    .participantAId("user_alice")
                    .participantBId("user_bob")
                    .build();

            EncryptedMessage msg1 = EncryptedMessage.builder().id("m1").conversationId("conv_100").build();
            EncryptedMessage msg2 = EncryptedMessage.builder().id("m2").conversationId("conv_100").build();

            when(conversationRepository.findById("conv_100")).thenReturn(Optional.of(conv));
            when(messageRepository.findByConversationIdOrderBySentAtAsc("conv_100")).thenReturn(List.of(msg1, msg2));

            List<EncryptedMessage> messages = messageService.getConversationMessages("user_bob", "conv_100");

            assertEquals(2, messages.size());
            verify(messageRepository, times(1)).findByConversationIdOrderBySentAtAsc("conv_100");
        }

        @Test
        @DisplayName("Should throw DomainException when conversation does not exist")
        void shouldThrowWhenConvNotFound() {
            when(conversationRepository.findById("non_existent")).thenReturn(Optional.empty());

            DomainException ex = assertThrows(DomainException.class, () ->
                    messageService.getConversationMessages("user_alice", "non_existent"));

            assertEquals("CONVERSATION_NOT_FOUND", ex.getErrorCode());
        }

        @Test
        @DisplayName("Should throw DomainException when requester is not a participant")
        void shouldThrowWhenRequesterNotParticipant() {
            Conversation conv = Conversation.builder()
                    .id("conv_100")
                    .participantAId("user_alice")
                    .participantBId("user_bob")
                    .build();

            when(conversationRepository.findById("conv_100")).thenReturn(Optional.of(conv));

            DomainException ex = assertThrows(DomainException.class, () ->
                    messageService.getConversationMessages("user_stranger", "conv_100"));

            assertEquals("UNAUTHORIZED_ACCESS", ex.getErrorCode());
        }
    }
}
